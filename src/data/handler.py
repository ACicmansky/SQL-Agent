import pandas as pd
from pathlib import Path

def load_data(file_path: str) -> pd.DataFrame:
    """Load data from a file."""
    df = pd.read_excel(file_path)

    # Rename the first column to 'ID'
    df.rename(columns={'Unnamed: 0': 'ID'}, inplace=True)

    # Set the name of the DataFrame to the name of the file
    df.name = Path(file_path).stem

    return df

def get_schema_from_dataframe(dataframe: pd.DataFrame) -> str:
    """Generates a CREATE TABLE SQL statement from a pandas DataFrame."""
    type_mapping = {
        "int64": "INT",
        "float64": "FLOAT",
        "object": "TEXT",
        "datetime64[ns]": "DATETIME",
    }

    columns = [f'"{col_name}" {type_mapping.get(str(dtype), "TEXT")}' for col_name, dtype in dataframe.dtypes.items()]
    return f"CREATE TABLE {dataframe.name} ({', '.join(columns)})"