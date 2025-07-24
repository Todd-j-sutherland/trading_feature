import streamlit as st
import pandas as pd
import json
from pathlib import Path

st.set_page_config(layout="wide")

def load_json_data(file_path):
    """Loads data from a JSON file."""
    if file_path.exists():
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            st.error(f"Error decoding JSON from {file_path}. File might be empty or corrupt.")
            return None
        except Exception as e:
            st.error(f"An error occurred while reading {file_path}: {e}")
            return None
    else:
        st.warning(f"File not found: {file_path}")
        return None

def main():
    """Main function to display the debug dashboard."""
    st.title("📊 ML Performance Data Debugger")
    st.write("This tool directly reads and displays the contents of the JSON data files used by the dashboards.")

    # Define the path to the data directory
    # This path is absolute on the remote server where this script will run
    data_dir = Path("/root/test/data/ml_performance")

    st.header("📍 Data Source")
    st.info(f"Reading data from: `{data_dir}`")

    # --- Display Prediction History ---
    st.header("📜 Prediction History")
    st.write("Shows the raw log of every prediction made by the `evening` command.")
    prediction_file = data_dir / "prediction_history.json"
    
    prediction_data = load_json_data(prediction_file)

    if prediction_data:
        df_predictions = pd.DataFrame(prediction_data)
        st.metric("Total Predictions Logged", len(df_predictions))
        
        # Display status counts
        if 'status' in df_predictions.columns:
            status_counts = df_predictions['status'].value_counts()
            st.write("Prediction Status Counts:")
            st.table(status_counts)

        st.dataframe(df_predictions)
    else:
        st.error("Could not load prediction history data.")


    # --- Display ML Performance History ---
    st.header("📈 ML Performance History")
    st.write("Shows the aggregated performance metrics, updated after predictions are resolved.")
    performance_file = data_dir / "ml_performance_history.json"

    performance_data = load_json_data(performance_file)

    if performance_data:
        df_performance = pd.DataFrame(performance_data)
        st.metric("Total Performance Records", len(df_performance))
        st.dataframe(df_performance)
    else:
        st.error("Could not load ML performance history data.")

if __name__ == "__main__":
    main()
