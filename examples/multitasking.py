import os
import json
import random
from pathlib import Path

import torch
import click
import evaluate
import numpy as np
from datasets import concatenate_datasets
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
# sacrebleu


SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
torch.backends.cudnn.deterministic = True


# given that this script is in examples/ directory
ROOT_DIR = Path(__file__).parent.parent

MAX_LENGTH = 512
LABEL_PAD_TOKEN_ID = -100
PATIENCE = 5

BLEU_METRIC = evaluate.load("sacrebleu")


def table_to_linear_with_prefix(table, dataset_name, dataset_obj, **kwargs):
    lin_table = dataset_obj.table_to_linear(table, **kwargs)
    return f'{dataset_name}: {lin_table}'


def calc_truncated(df):
    n_truncated_inputs = 0
    n_truncated_outputs = 0
    for item in df:
        if item['input_ids'].size[-1] == MAX_LENGTH:
            n_truncated_inputs += 1
        if item['labels'].size[-1] == MAX_LENGTH:
            n_truncated_outputs += 1

    p_truncated_inputs = round(n_truncated_inputs / df.num_rows, 4)
    p_truncated_outputs = round(n_truncated_outputs / df.num_rows, 4)
    return p_truncated_inputs, p_truncated_outputs


def compute_bleu(eval_preds, tokenizer):
    preds, labels = eval_preds
    if isinstance(preds, tuple):
        preds = preds[0]

    decoded_preds = tokenizer.batch_decode(preds, skip_special_tokens=True)
    labels = np.where(labels != LABEL_PAD_TOKEN_ID, labels, tokenizer.pad_token_id)
    decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)

    result = BLEU_METRIC.compute(predictions=decoded_preds, references=decoded_labels)
    result = {"bleu": result["score"]}

    prediction_lens = [np.count_nonzero(pred != tokenizer.pad_token_id) for pred in preds]
    result["gen_len"] = np.mean(prediction_lens)
    result = {k: round(v, 4) for k, v in result.items()}

    return result


@click.command()
@click.option("--datasets", "-d", required=True, type=str, help="Datasets to train on")
@click.option("--base-model", "-m", default="t5-small", type=str, help="Base model to finetune")
@click.option("--epochs", "-e", default=30, type=int, help="Maximum number of epochs")
@click.option("--batch-size", "-b", default=16, type=int, help="Path to the output directory")
@click.option("--ckpt-dir", "-c", default=os.path.join(ROOT_DIR, "checkpoints"), type=str, help="Directory to store checkpoints")
@click.option("--output-dir", "-o", default=os.path.join(ROOT_DIR, "models"), type=str, help="Directory to store models and their outputs")
def main(datasets, base_model, epochs, batch_size, ckpt_dir, output_dir):
    os.makedirs(ckpt_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    model_name = f'{base_model.rsplit("/", 1)[-1]}_{datasets}_{epochs}e_{batch_size}bs'
    print(f'Fine-tuning {model_name}')

    save_dir = os.path.join(output_dir, model_name)
    os.makedirs(save_dir, exist_ok=True)
    os.makedirs(os.path.join(save_dir, "preds"), exist_ok=True)
    os.makedirs(os.path.join(save_dir, "scores"), exist_ok=True)

    model = AutoModelForSeq2SeqLM.from_pretrained(base_model)
    tokenizer = AutoTokenizer.from_pretrained(base_model)

    datasets = datasets.split(',')
    hf_datasets = {}

    for dataset in datasets:
        tg_dataset = load_dataset(dataset)
        hf_datasets[dataset] = {
            p: tg_dataset.get_hf_dataset(
                split=p,
                tokenizer=tokenizer,
                max_length=MAX_LENGTH,
                linearize_fn=table_to_linear_with_prefix,
                linearize_params={
                    'dataset_name': dataset,
                    'dataset_obj': tg_dataset
                    # any other dataset-specific kwargs
                }
            )
            for p in tg_dataset.splits
        }
        print(tokenizer.decode(hf_datasets[dataset]['train'][0]['input_ids']))

    joint_train = concatenate_datasets([x['train'] for x in hf_datasets.values()])
    joint_train = joint_train.shuffle(seed=SEED)

    joint_dev = concatenate_datasets([x['dev'] for x in hf_datasets.values()])
    joint_dev = joint_dev.shuffle(seed=SEED)

    collator = DataCollatorForSeq2Seq(
        tokenizer,
        model=model,
        label_pad_token_id=LABEL_PAD_TOKEN_ID
    )

    def compute_dev_metrics(eval_preds):
        return compute_bleu(eval_preds, tokenizer)

    training_args = Seq2SeqTrainingArguments(
        output_dir=os.path.join(ckpt_dir, model_name),
        report_to='none',
        evaluation_strategy='epoch',
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        learning_rate=1e-4,
        num_train_epochs=epochs,
        save_strategy='epoch',
        save_total_limit=2,
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
        train_dataset=joint_train,
        eval_dataset=joint_dev,
        tokenizer=tokenizer,
        data_collator=collator,
        compute_metrics=compute_dev_metrics,
        callbacks=[
            EarlyStoppingCallback(early_stopping_patience=PATIENCE)
        ]
    )

    trainer.train()
    trainer.save_model(os.path.join(save_dir, "model"))

    for dataset in datasets:
        for part in ['dev', 'test']:
            print(f'Running prediction on {part}')

            preds = trainer.predict(hf_datasets[dataset][part])
            decoded_preds = tokenizer.batch_decode(preds.predictions, skip_special_tokens=True)
            decoded_preds = [{'out': [p]} for p in decoded_preds]

            filename = f'{base_model}_{dataset}_{part}'

            with open(os.path.join(save_dir, "preds", f'preds_{filename}.jsonl'), 'w') as f:
                f.write('\n'.join(json.dumps(pred, ensure_ascii=False) for pred in decoded_preds))

            with open(os.path.join(save_dir, "scores", f'scores_{filename}.txt'), 'w') as f:
                f.write(f'SacreBLEU: {preds.metrics["test_bleu"]}')


if __name__ == '__main__':
    main()
