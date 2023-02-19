import os
import json
from pathlib import Path

import click
import evaluate
import numpy as np
from transformers import (
    AutoModelForSeq2SeqLM, AutoTokenizer,
    DataCollatorForSeq2Seq, Seq2SeqTrainingArguments,
    Seq2SeqTrainer, EarlyStoppingCallback
)

from tabgenie import load_dataset


# extra requirements:
# numpy
# evaluate
# transformers==4.25.1
# torch==1.12.1+cu113 --extra-index-url https://download.pytorch.org/whl/cu113


# given that this script is in examples/ directory
ROOT_DIR = Path(__file__).parent.parent

LABEL_PAD_TOKEN_ID = -100
PATIENCE = 5
N_EVALS = 20

BLEU_METRIC = evaluate.load("sacrebleu")


def compute_bleu(eval_preds, tokenizer):
    preds, labels = eval_preds
    if isinstance(preds, tuple):
        preds = preds[0]

    decoded_preds = tokenizer.batch_decode(preds, skip_special_tokens=True)
    labels = np.where(labels != -100, labels, tokenizer.pad_token_id)
    decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)

    result = BLEU_METRIC.compute(predictions=decoded_preds, references=decoded_labels)
    result = {"bleu": result["score"]}

    prediction_lens = [np.count_nonzero(pred != tokenizer.pad_token_id) for pred in preds]
    result["gen_len"] = np.mean(prediction_lens)
    result = {k: round(v, 4) for k, v in result.items()}

    return result


@click.command()
@click.option("--dataset", "-d", required=True, type=str, help="Dataset to train on")
@click.option("--base-model", "-m", default="t5-small", type=str, help="Base model to finetune")
@click.option("--epochs", "-e", default=10, type=int, help="Maximum number of epochs")
@click.option("--batch-size", "-b", default=16, type=int, help="Path to the output directory")
@click.option("--ckpt-dir", "-c", default=ROOT_DIR / "checkpoints", type=int, help="Directory to store checkpoints")
@click.option("--output-dir", "-o", default=ROOT_DIR / "models", type=int, help="Directory to store models and their outputs")
def main(dataset, base_model, epochs, batch_size, ckpt_dir, output_dir):
    os.makedirs(ckpt_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    model_name = f'{base_model.rsplit("/", 1)[-1]}_{dataset}_{epochs}e_{batch_size}bs'
    print(f'Fine-tuning {model_name}')

    save_dir = output_dir / model_name
    os.makedirs(save_dir, exist_ok=True)
    os.makedirs(save_dir / "preds", exist_ok=True)
    os.makedirs(save_dir / "scores", exist_ok=True)

    model = AutoModelForSeq2SeqLM.from_pretrained(base_model)
    tokenizer = AutoTokenizer.from_pretrained(base_model)

    tg_dataset = load_dataset(dataset)
    hf_datasets = {
        p: tg_dataset.get_hf_dataset(split=p, tokenizer=tokenizer)
        for p in tg_dataset.splits
    }

    collator = DataCollatorForSeq2Seq(
        tokenizer,
        model=model,
        label_pad_token_id=LABEL_PAD_TOKEN_ID
    )

    eval_steps = int((hf_datasets['train'].num_rows * epochs / batch_size) / N_EVALS)

    def compute_dev_metrics(eval_preds):
        return compute_bleu(eval_preds, tokenizer)

    training_args = Seq2SeqTrainingArguments(
        output_dir=str(ckpt_dir / model_name),
        report_to='none',
        evaluation_strategy='steps',
        eval_steps=eval_steps,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        learning_rate=1e-4,
        num_train_epochs=epochs,
        save_strategy='steps',
        save_total_limit=2,
        save_steps=eval_steps,
        predict_with_generate=True,
        generation_max_length=512,
        generation_num_beams=3,
        metric_for_best_model='eval_bleu',
        greater_is_better=True,
        load_best_model_at_end=True
    )

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=hf_datasets['train'],
        eval_dataset=hf_datasets['dev'],
        tokenizer=tokenizer,
        data_collator=collator,
        compute_metrics=compute_dev_metrics,
        callbacks=[
            EarlyStoppingCallback(early_stopping_patience=PATIENCE)
        ]
    )

    trainer.train()
    trainer.save_model(str(save_dir / "model"))

    for part in ['dev', 'test']:
        preds = trainer.predict(hf_datasets[part])
        decoded_preds = tokenizer.batch_decode(preds.predictions, skip_special_tokens=True)
        decoded_preds = [{'out': [p]} for p in decoded_preds]

        with open(save_dir / "preds" / f'preds_{base_model}_{dataset}_{part}.jsonl', 'w') as f:
            f.write('\n'.join(json.dumps(pred) for pred in decoded_preds))

        with open(save_dir / "scores" / f'scores_{base_model}_{dataset}_{part}.txt', 'w') as f:
            f.write(f'SacreBLEU: {preds.metrics["test_bleu"]}')


if __name__ == '__main__':
    main()
