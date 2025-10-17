import pandas as pd
from pathlib import Path
from datetime import datetime

# Import the logger from the logging module
from src.assistant.utils.logging import logger, setup_logger
from src.assistant.fetchers.wrds_crsp import fetch_crsp_monthly_returns
from src.factors.momentum import calculate_12_1_momentum

# Ensure logger is set up
setup_logger()


def run_analysis():
    """
    Run the full momentum factor analysis using WRDS.

    This script fetches CRSP monthly returns for a list of PERMNOs, calculates
    the 12-1 momentum factor, and saves the results to a CSV file.
    """
    # Define a list of PERMNOs to analyze (sample tech stocks for now)
    permnos = [10107, 12490, 14593, 11850]  # Example PERMNOs

    # Log the start of the process
    logger.info("Starting momentum factor analysis...")

    try:
        # Fetch CRSP monthly returns for the last 5 years
        start_date = (datetime.now() - pd.DateOffset(years=5)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        crsp_data = fetch_crsp_monthly_returns(permnos, start_date=start_date, end_date=end_date)

        # Convert the data into a pandas DataFrame
        crsp_df = pd.DataFrame(crsp_data)

        # Calculate the 12-1 momentum factor
        momentum_df = calculate_12_1_momentum(crsp_df)

        # Create the artifacts directory if it doesn't exist
        artifacts_dir = Path("artifacts")
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        # Save the results to a CSV file
        output_file = artifacts_dir / f"momentum_{datetime.now().strftime('%Y-%m-%d')}.csv"
        momentum_df.to_csv(output_file, index=False)

        # Log a success message
        logger.info(
            f"Momentum factor analysis completed successfully. Results saved to {output_file}"
        )

    except Exception as e:
        # Log any errors that occur
        logger.error(f"An error occurred during momentum factor analysis: {e}")


if __name__ == "__main__":
    run_analysis()
