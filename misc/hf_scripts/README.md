# Huggingface datasets scripts

This folder contains scripts used to newly upload some of the datasets in TabGenie to [Huggingface Datasets](https://huggingface.co/datasets). 

The structure of the scripts is based on the existing scripts and a tutorial which may be found [here](https://huggingface.co/docs/datasets/dataset_script).

The field `DATASET_PATH` has to point to the original dataset repository.

Note that some newer versions of the `datasets` package create an empty `README.md` file which overrides the information in the loading script and the info then does not show up in the app. To prevent this behavior, use either `datasets==2.5.1` or delete the `README.md` after dataset upload.