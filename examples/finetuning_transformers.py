import os
import json
import random
from pathlib import Path

import torch
import click
import evaluate
import numpy as np
from tqdm import tqdm
from torch.utils.data import DataLoader
from transformers import (
    AutoModelForSeq2SeqLM, AutoTokenizer,
    DataCollatorForSeq2Seq, Seq2SeqTrainingArguments,
    Seq2SeqTrainer, EarlyStoppingCallback
)

from tabgenie import load_dataset


DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
torch.backends.cudnn.deterministic = True


# given that this script is in examples/ directory
ROOT_DIR = Path(__file__).parent.parent

MAX_LENGTH = 512
MAX_OUT_LENGTH = 512
LABEL_PAD_TOKEN_ID = -100
NUM_BEAMS = 3

BLEU_METRIC = evaluate.load("sacrebleu")


def calc_truncated(df):
    n_truncated_inputs = 0
    n_truncated_outputs = 0
    for item in df:
        if item['input_ids'].size()[-1] == MAX_LENGTH:
            n_truncated_inputs += 1
        if item['labels'].size()[-1] == MAX_LENGTH:
            n_truncated_outputs += 1

    p_truncated_inputs = round(n_truncated_inputs / df.num_rows, 4)
    p_truncated_outputs = round(n_truncated_outputs / df.num_rows, 4)
    return p_truncated_inputs, p_truncated_outputs


def compute_bleu_on_one_reference(eval_preds, tokenizer):
    # THIS FUNCTION IS COMPARING ONLY WITH ONE REFERENCE,
    # USED ONLY FOR INTERMEDIATE EVALUATION

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


def compute_bleu_on_all_references(preds, references):
    # padding references
    max_ref_len = max(len(x) for x in references)
    min_ref_len = min(len(x) for x in references)
    if max_ref_len == 0:
        return None

    print(f'Number of refs for one table: max {max_ref_len}, min {min_ref_len}')

    references = [x + ['' for _ in range(max_ref_len - len(x))] for x in references]
    result = BLEU_METRIC.compute(predictions=preds, references=references)

    return result["score"]


def run_prediction(dataset, model, tokenizer, batch_size, num_beams=1):
    all_preds = []
    model.eval()

    collator = DataCollatorForSeq2Seq(
        tokenizer,
        model=model,
        label_pad_token_id=LABEL_PAD_TOKEN_ID
    )

    tokens = dataset.remove_columns([c for c in dataset.column_names if c not in tokenizer.model_input_names])
    test_dataloader = DataLoader(tokens, batch_size=batch_size, collate_fn=collator)

    with torch.no_grad():
        for batch in tqdm(test_dataloader):
            batch = {k: v.to(DEVICE) for k, v in batch.items()}
            preds = model.generate(
                **batch,
                num_beams=num_beams,
                max_length=MAX_OUT_LENGTH
            )
            decoded_preds = tokenizer.batch_decode(preds, skip_special_tokens=True)
            all_preds.extend(decoded_preds)

    if 'references' in dataset.column_names:
        score = compute_bleu_on_all_references(all_preds, dataset['references'])
    else:
        score = None

    return all_preds, score


def write_results(save_dir, filename, preds, score):
    with open(os.path.join(save_dir, "preds", f'preds_{filename}.jsonl'), 'w') as f:
        f.write(
            '\n'.join(
                json.dumps({'out': [pred]}, ensure_ascii=False)
                for pred in preds
            )
        )

    with open(os.path.join(save_dir, "scores", f'scores_{filename}.txt'), 'w') as f:
        f.write(f'SacreBLEU: {score}')


@click.command()
@click.option("--dataset", "-d", required=True, type=str, help="Dataset to train on")
@click.option("--base-model", "-m", default="t5-small", type=str, help="Base model to finetune")
@click.option("--epochs", "-e", default=30, type=int, help="Maximum number of epochs")
@click.option("--batch-size", "-b", default=16, type=int, help="Path to the output directory")
@click.option("--ckpt-dir", "-c", default=os.path.join(ROOT_DIR, "checkpoints"), type=str, help="Directory to store checkpoints")
@click.option("--output-dir", "-o", default=os.path.join(ROOT_DIR, "models"), type=str, help="Directory to store models and their outputs")
def main(dataset, base_model, epochs, batch_size, ckpt_dir, output_dir):
    os.makedirs(ckpt_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    model_name = f'{base_model.rsplit("/", 1)[-1]}_{dataset}_{epochs}e_{batch_size}bs'
    print(f'Fine-tuning {model_name}')

    save_dir = os.path.join(output_dir, model_name)
    model_ckpt_dir = os.path.join(ckpt_dir, model_name)
    os.makedirs(save_dir, exist_ok=True)
    os.makedirs(os.path.join(save_dir, "preds"), exist_ok=True)
    os.makedirs(os.path.join(save_dir, "scores"), exist_ok=True)

    model = AutoModelForSeq2SeqLM.from_pretrained(base_model)
    tokenizer = AutoTokenizer.from_pretrained(base_model)

    tg_dataset = load_dataset(dataset)
    hf_datasets = {
        p: tg_dataset.get_hf_dataset(split=p, tokenizer=tokenizer, max_length=MAX_LENGTH)
        for p in tg_dataset.splits
    }
    print(hf_datasets)

    # to control if the data fits into the predefined length limit
    p_truncated_inputs, p_truncated_outputs = calc_truncated(hf_datasets['train'])
    print(f'Truncated inputs: {p_truncated_inputs}')
    print(f'Truncated outputs: {p_truncated_outputs}')

    collator = DataCollatorForSeq2Seq(
        tokenizer,
        model=model,
        label_pad_token_id=LABEL_PAD_TOKEN_ID
    )

    def compute_dev_metrics(eval_preds):
        return compute_bleu_on_one_reference(eval_preds, tokenizer)

    training_args = Seq2SeqTrainingArguments(
        output_dir=os.path.join(ckpt_dir, model_name),
        report_to='none',
        evaluation_strategy='epoch',
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        learning_rate=1e-4,
        num_train_epochs=epochs,
        save_strategy='epoch',
        predict_with_generate=True,
        generation_max_length=512,
        metric_for_best_model='eval_bleu',
        greater_is_better=True
    )

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=hf_datasets['train'],
        eval_dataset=hf_datasets['dev'],
        tokenizer=tokenizer,
        data_collator=collator,
        compute_metrics=compute_dev_metrics
    )

    trainer.train()

    # choosing the best model among checkpoints
    ckpts = os.listdir(model_ckpt_dir)
    score_vals = {}

    for ckpt_name in ckpts:
        ckpt_path = os.path.join(model_ckpt_dir, ckpt_name)
        os.makedirs(os.path.join(ckpt_path, 'preds'), exist_ok=True)
        print(f'Running prediction of {ckpt_name} on dev')

        ckpt_model = AutoModelForSeq2SeqLM.from_pretrained(ckpt_path).to(DEVICE)

        preds, score = run_prediction(
            dataset=hf_datasets['dev'],
            model=ckpt_model,
            tokenizer=tokenizer,
            batch_size=batch_size,
            num_beams=NUM_BEAMS
        )
        score_vals[ckpt_path] = {'score': score, 'preds': preds}
        print(f'BLEU score for {ckpt_name}: {score}')

    # saving best model and its dev results
    max_ckpt_path, max_ckpt_results = max(score_vals.items(), key=lambda x: x[1]['score'])
    print(f"Max BLEU score: {max_ckpt_results['score']} for {max_ckpt_path}")

    best_ckpt_model = AutoModelForSeq2SeqLM.from_pretrained(max_ckpt_path).to(DEVICE)
    best_ckpt_model.save_pretrained(os.path.join(save_dir, "model"))

    write_results(
        save_dir,
        filename=f'{base_model}_{dataset}_dev',
        preds=max_ckpt_results['preds'],
        score=max_ckpt_results['score']
    )

    # final prediction on test
    test_preds, test_score = run_prediction(
        dataset=hf_datasets['test'],
        model=best_ckpt_model,
        tokenizer=tokenizer,
        batch_size=batch_size,
        num_beams=NUM_BEAMS
    )

    write_results(
        save_dir,
        filename=f'{base_model}_{dataset}_test',
        preds=test_preds,
        score=test_score
    )


if __name__ == '__main__':
    main()
