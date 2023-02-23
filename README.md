# 🧞 TabGenie

A toolkit for interactve table-to-text generation.

**Demo :point_right: https://quest.ms.mff.cuni.cz/rel2text/tabgenie**

## Project overview

### Main features 
- visualization of data-to-text generation datasets
- interactive processing pipelines
- unified Python data loaders
- preparing a spreadsheet for error analysis
- exporting tables to various file formats

 ### Frontend Preview

![preview](img/preview.png)

### About
TabGenie provides access to **data-to-text generation datasets** in a unified tabular format. The datasets are loaded from the [HuggingFace datasets](https://huggingface.co/datasets) and visualized in a custom web interface.

Each table in a dataset is displayed in a tabular format:
- each table contains M rows and N columns,
- cells may span multiple columns or rows,
- cells may be marked as headings (indicated by bold font),
- cells may be highlighted (indicated by yellow background).

Additionally, each example may contain metadata (such as title, url, etc.) which are displayed next to the main table as *properties*.


## Quickstart
```
pip install tabgenie
tabgenie run --host=127.0.0.1
```
### Demo
**:point_right: https://quest.ms.mff.cuni.cz/rel2text/tabgenie**


## Datasets

See `src/loaders/data.py` for an up-to-date list of available datasets.
| Dataset                                                                              | Source                    | Data type      | # train | # dev  | # test | License     |
| ------------------------------------------------------------------------------------ | ------------------------- | -------------- | ------- | ------ | ------ | ----------- |
| **[CACAPO](https://huggingface.co/datasets/kasnerz/cacapo)**                         | van der Lee et al. (2020) | Key-value      | 15,290  | 1,831  | 3,028  | CC BY       |
| **[DART](https://huggingface.co/datasets/GEM/dart)**                                 | Nan et al. (2021)         | Graph          | 62,659  | 2,768  | 5,097  | MIT         |
| **[E2E](https://huggingface.co/datasets/GEM/e2e_nlg)**                               | Dušek et al. (2019)       | Key-value      | 33,525  | 1,484  | 1,847  | CC BY-SA    |
| **[EventNarrative](https://huggingface.co/datasets/kasnerz/eventnarrative)**         | Colas et al. (2021)       | Graph          | 179,544 | 22,442 | 22,442 | CC BY       |
| **[HiTab](https://huggingface.co/datasets/kasnerz/hitab)**                           | Cheng et al. (2021)       | Table          | 7,417   | 1,671  | 1,584  | C-UDA       |
| **[Chart-to-text](https://huggingface.co/datasets/kasnerz/charttotext-s)**           | Kantharaj et al. (2022)   | Chart          | 24,368  | 5,221  | 5,222  | GNU GPL     |
| **[Logic2Text](https://huggingface.co/datasets/kasnerz/logic2text)**                 | Chen et al. (2020b)       | Table  + Logic | 8,566   | 1,095  | 1,092  | MIT         |
| **[LogicNLG](https://huggingface.co/datasets/kasnerz/logicnlg)**                     | Chen et al. (2020a)       | Table          | 28,450  | 4,260  | 4,305  | MIT         |
| **[NumericNLG](https://huggingface.co/datasets/kasnerz/numericnlg)**                 | Suadaa et al. (2021)      | Table          | 1,084   | 136    | 135    | CC BY-SA    |
| **[SciGen](https://huggingface.co/datasets/kasnerz/scigen)**                         | Moosavi et al. (2021)     | Table          | 13,607  | 3,452  | 492    | CC BY-NC-SA |
| **[SportSett:Basketball](https://huggingface.co/datasets/GEM/sportsett_basketball)** | Thomson et al. (2020)     | Table          | 3,690   | 1,230  | 1,230  | MIT         |
| **[ToTTo](https://huggingface.co/datasets/totto)**                                   | Parikh et al. (2020)      | Table          | 121,153 | 7,700  | 7,700  | CC BY-SA    |
| **[WebNLG](https://huggingface.co/datasets/GEM/web_nlg)**                            | Ferreira et al. (2020)    | Graph          | 35,425  | 1,666  | 1,778  | CC BY-NC    |
| **[WikiBio](https://huggingface.co/datasets/wiki_bio)**                              | Lebret et al. (2016)      | Key-value      | 582,659 | 72,831 | 72,831 | CC BY-SA    |
| **[WikiSQL](https://huggingface.co/datasets/wikisql)**                               | Zhong et al. (2017)       | Table + SQL    | 56,355  | 8,421  | 15,878 | BSD         |
| **[WikiTableText](https://huggingface.co/datasets/kasnerz/wikitabletext)**           | Bao et al. (2018)         | Key-value      | 10,000  | 1,318  | 2,000  | CC BY       |


## Requirements
- Python 3
- Flask
- HuggingFace datasets

See `setup.py` for the full list of requirements.

## Installation
- **pip**: `pip install tabgenie`
- **development**: `pip install -e .[dev]`
- **deployment**: `pip install -e .[deploy]`

## Web interface
- **local development**: `tabgenie [app parameters] run [--port=PORT] [--host=HOSTNAME]`
- **deployment**: `gunicorn "src.tabgenie.cli:create_app([app parameters])"`

## Command-line Interface
### Export data
Exports individual tables to file.

Usage:
```
tabgenie export \
  --dataset DATASET_NAME \
  --split SPLIT \
  --out_dir OUT_DIR \
  --export_format EXPORT_FORMAT
```
Supported formats: `json`, `csv`, `xlsx`, `html`, `txt`.

### Spreadsheet for error analysis
Generates a spreadsheet with outputs and randomly selected examples for manual error analysis.

Usage:
```
tabgenie spreadsheet \
  --dataset DATASET  \
  --split SPLIT \
  --in_file IN_FILE  \
  --out_file OUT_FILE \
  --count EXAMPLE_COUNT
```

### Info
Displays information about the dataset in YAML format (or the list of available datasets if no argument is provided).

```
tabgenie info [-d DATASET]
```

## Python
If your code is based on Huggingface datasets, you can use the following snippet to get the Huggingface dataset object with linearized and tokenized tables:

```python
from transformers import AutoTokenizer
import tabgenie as tg

dataset_name = "totto"
split = "train"
tokenizer = AutoTokenizer(...)

tg_dataset = tg.load_dataset(dataset_name)
hf_dataset = tg_dataset.get_hf_dataset(
            split=split,
            tokenizer=tokenizer,
)
```

The method `get_hf_dataset()` optionally accepts a parameter `linearize_fn` which is a function taking an argument of type `data.structs.Table` and returning a `str`. This can be used for custom table linearization.

By default, this uses the `table_to_linear` function of the dataset (which can be also overridden in subclasses).



## HuggingFace Integration
The datasets are stored to `HF_DATASETS_CACHE` directory which defaults to `~/.cache/huggingface/`. Set the
environment variable before launching any tabgenie command to store the potentially very large datasets to different
directory. However, be consistent across all usage of Tabgenie commands.


The datasets are all loaded from [HuggingFace datasets](https://huggingface.co/datasets) instead of their original repositories. This allows to use preprocessed datasets and a single unified loader.

Note that there may be some minor changes in the data w.r.t. to the original datasets due to unification, such as adding "subject", "predicate" and "object" headings to RDF triple-to-text datasets.

The metadata for each table are displayed as `properties` next to the main table.

## Adding datasets
For adding a new dataset:
- prepare the dataset
  - [add the dataset to Huggingface Datasets](https://huggingface.co/docs/datasets/upload_dataset)
  - OR: download the dataset locally
- create the dataset loader in `src/loaders`
  - a subclass of `HFTabularDataset` for HF datasets
  - a subclass of `TabularDataset` for local datasets
- add the dataset name to `config.yml`.

Each dataset should contain the `prepare_table(split, table_idx)` method which instantiates a `Table` object from the raw data saved in `self.data`.

The `Table` object is automatically exported to HTML and other formats (the methods may be overridden).

If a dataset is an instance of `HFTabularDataset` (i.e. is loaded from Huggingface Datasets), it should contain a `self.hf_id` attribute. The attribute is used to automatically load the dataset via `datasets` package.

## Interactive mode
Pipelines are used for processing the tables and producing outputs.

See `src/processing/processing.py` for an up-to-date list of available pipelines.
- **model_api** - a pipeline which generates a textual description of a table by calling a table-to-text generation model through API,
- **graph** - a pipeline which creates a knowledge graph by extracting RDF triples from a table and visualizes the output using D3.js library,

### Adding pipelines
For adding a new pipeline:
- create a file in `src/processing/pipelines` containing the pipeline class,
- create file(s) in `src/processing/processors` with processors needed for the pipeline,
- add the mapping between pipeline name and class name to `get_pipeline_class_by_name()` in `src/processing/processing.py`. 

Each pipeline should define `self.processors` in the `__init__()` method, instantiating the processors needed for the pipeline.

The input to each pipeline is a `content` object containing several fields needed for table processing. This interface is subject to change (see `src/__init.py_:run_pipeline()` for more details).

The processors serve as modules, i.e. existing processors can be combined to create new pipelines. The interface between the processors may vary, it is however expected that the last processor in the pipeline outputs HTML code which is displayed on the page.

## Configuration
The global configuration is stored in the `config.yml` file.

- `datasets` - datasets which will be available in the web interface,
- `default_dataset` - the dataset which is loaded by default,
- `host_prefix` - subdirectory on which the app is deployed (used for loading static files and sending POST requests),
- `cache_dev_splits` - whether to preload all available dev sets after startup,
- `generated_outputs_dir` - directory from which the generated outputs are loaded,
- `pipelines` - pipelines which will be available in the web interface (see the *Interactive mode* section for more info).