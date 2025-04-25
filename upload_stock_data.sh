#!/bin/bash

print_usage() {
    echo "Usage: $0 <api_url> <ticker> <start_time> <end_time> <csv_file> [--dry-run]"
    echo ""
    echo "Arguments:"
    echo "  api_url    The base URL of the API  (e.g., http://localhost:8000)"
    echo "  ticker     The stock ticker symbol (e.g., AAPL)"
    echo "  start_time The start time for the stock data (format: YYYY-MM-DD)"
    echo "  end_time   The end time for the stock data (format: YYYY-MM-DD)"
    echo "  csv_file   The path to the CSV file containing stock data."
    echo ""
    echo "Example:"
    echo "  $0 http://localhost:8001 AAPL 2023-01-01 2023-01-31 stock_data.csv"
}

delete_stock_data() {
    local api_url=$1
    local ticker=$2

    echo "Deleting existing stock data for ticker: $ticker"
    RESPONSE=$(curl -s -w "\n%{http_code}" -X DELETE "$api_url/stock_vault/$ticker")
    HTTP_BODY=$(echo "$RESPONSE" | sed '$d')
    HTTP_STATUS=$(echo "$RESPONSE" | tail -n 1)
    if [[ $HTTP_STATUS -ne 200 ]]; then
        echo "Error: Failed to delete existing stock data."
        echo "HTTP Status: $HTTP_STATUS"
        echo "Response: $HTTP_BODY"
        exit 1
    fi
    echo "Existing stock data for ticker $ticker deleted successfully."
}

checking_stock_catalog() {
    local api_url=$1
    local ticker=$2

    echo "Checking stock catalog for ticker: $ticker"
    RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$api_url/stock_vault/catalog/$ticker")
    HTTP_BODY=$(echo "$RESPONSE" | sed '$d')
    HTTP_STATUS=$(echo "$RESPONSE" | tail -n 1)

    if [[ $HTTP_STATUS -ne 200 ]]; then
        echo "Error: Failed to check stock catalog."
        echo "HTTP Status: $HTTP_STATUS"
        echo "Response: $HTTP_BODY"
        exit 1
    fi

    # Check if the 'data' field is null
    DATA=$(echo "$HTTP_BODY" | jq -r '.data')
    if [[ $DATA == "null" ]]; then
        return 1
    fi

    echo "Warning: Stock catalog for ticker $ticker exists."
    return 0
}

if [[ $# -lt 5 ]]; then
    echo "Error: Insufficient arguments provided."
    print_usage
    exit 1
fi

API_URL=$1
TICKER=$2
START_TIME=$3
END_TIME=$4
CSV_FILE=$5
DRY_RUN=false

if [[ $# -eq 6 && $6 == "--dry-run" ]]; then
    DRY_RUN=true
fi

if [[ ! -f $CSV_FILE ]]; then
    echo "Error: CSV file not found at path: $CSV_FILE"
    exit 1
fi
echo "Payload: {\"ticker\": \"$TICKER\", \"start_time\": \"$START_TIME\", \"end_time\": \"$END_TIME\", \"csv_file\": \"$(cat $CSV_FILE)\"}"

# Check if stock vault catalog exists
if checking_stock_catalog "$API_URL" "$TICKER"; then
    # Prompt user for confirmation
    read -p "Stock catalog exists for ticker $TICKER. Do you want to delete it? (y/n): " CONFIRM
    if [[ $CONFIRM != "y" ]]; then
        echo "Deletion canceled by user. Exiting."
        exit 0
    fi

    # Delete exisiting stock data for the ticker
    delete_stock_data "$API_URL" "$TICKER"
fi

# Call the API to start the bulk insert
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/stock_vault/import" \
    -F "ticker=$TICKER" \
    -F "start_time=$START_TIME" \
    -F "end_time=$END_TIME" \
    -F "csv_file=@$CSV_FILE")

HTTP_BODY=$(echo "$RESPONSE" | sed '$d')
HTTP_STATUS=$(echo "$RESPONSE" | tail -n 1)
echo "$RESPONSE"
if [[ $HTTP_STATUS -ne 200 ]]; then
    echo "Error: Failed to start bulk insert."
    echo "HTTP Status: $HTTP_STATUS"
    echo "Response: $HTTP_BODY"
    exit 1
fi

TASK_ID=$(echo "$HTTP_BODY" | jq -r '.task_id')
if [[ -z $TASK_ID || $TASK_ID == "null" ]]; then
    echo "Error: Failed to retrieve task_id from the response."
    exit 1
fi

echo "Bulk insert started. Task ID: $TASK_ID"

# Polling for task status
while true; do
    STATUS_RESPONSE=$(curl -s "$API_URL/task_status/$TASK_ID")
    STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.status')

    echo "Task Status: $STATUS"

    if [[ $STATUS == "Completed" ]]; then
        echo "Bulk insert completed successfully."
        break
    elif [[ $STATUS == Failed* ]]; then
        echo "Bulk insert failed."
        break
    fi

    sleep 5
done

if [[ $DRY_RUN == true ]]; then
    echo "Dry run enabled. Deleting imported stock data for ticker: $TICKER"
    delete_stock_data "$API_URL" "$TICKER"
    echo "Dry run completed. No data was actually uploaded."
fi