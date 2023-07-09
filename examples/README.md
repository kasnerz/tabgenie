# Training examples

You can load the datasets in a unified way for training the models.


## Requirements
Please, first install the additional requirements listed in `./requirements.txt`.

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

## Multi-tasking

The example `multitasking.py` is almost equivalent to `finetuning_transformers.py` (section above). The only parameter difference is:
* `--datasets` or `-d` - names of the datasets (listed in `loaders.DATASET_CLASSES`) separated by comma, e.g. `e2e,webnlg`.

Dataset-specific task description is prepended to each input item before training. <br>
In this example, custom linearization functions are implemented for E2E and WebNLG datasets.

