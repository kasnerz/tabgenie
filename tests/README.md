**Autotests**  

Autotests check every table in all datasets. To exclude a dataset, comment it out in ```tabgenie/loaders/__init__.py```. To exclude split, you need to comment it out in ```tests/conftest.py```.
At the moment, the following autotests are ready:

  - **test_table** it checks the processing of each table by the function prepare_table().    
To run the test, enter into the terminal:  
   ```pytest tests/test_prepare_table.py```
  - **test_export** It checks whether each table can be exported to the following formats:  
   ✅ table_to_json  
   ✅ table_to_excel  
   ✅ table_to_csv  
   ✅ table_to_df  
   ✅ table_to_html  
   ❌ table_to_triples  
   To run the test, enter into the terminal:  
   ```pytest tests/test_export.py```
  - **test_row_eq_len** It checks that all table rows have the same length, i.e. squareness check.    
To run the test, enter into the terminal:  
   ```pytest tests/test_row_eq_len.py```

**Quickstart**
```
pip install pytest
pytest tests/
```
