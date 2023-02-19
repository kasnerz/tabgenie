# Training examples

You can load the datasets in a unified way for training the models.

## Fine-tuning using `transformers` library
`finetuning_transformers.py` is an example of fine-tuning a seq2seq model and running inference using `transformers` library. It can be run from the command line, e.g. :
```
python examples/finetuning_transformers.py -d e2e
```
Parameters:
* `--dataset` or `-d` - name of the dataset (listed in `loaders.DATASET_CLASSES`).
* `--base-model` or `-m` - HF name of the base model to fine-tune. Default: `t5-small`.
* `--epochs` or `-e` - maximum number of epochs (patience of 5 is applied during training). Default: 30.
* `--batch-size` or `-b` - batch size. Default: 16.
* `--ckpt-dir` or `-c` - path to folder for storing checkpoints. Default: `PROJECT_ROOT/checkpoints`.
* `--model-dir` or `-m` - path to folder for storing models and outputs. Default: `PROJECT_ROOT/models`.

Requirements to run the example (in addition to `tabgenie`):
* `numpy`
* `evaluate`
* `transformers==4.25.1`
* `torch==1.12.1+cu113 --extra-index-url https://download.pytorch.org/whl/cu113`
* `sacrebleu`