import joblib
import io
import os
import boto3
from PIL import Image
from ai_edge_litert.interpreter import Interpreter
from dotenv import load_dotenv
load_dotenv(override=True)

S3_BUCKET   = os.getenv("S3_BUCKET")
S3_DATA_KEY = "churn/data/telco_churn.csv"
S3_CHURN_MODEL_PREFIX = "churn/models/"
S3_XRAY_MODEL_PREFIX = "xray/models/"

s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION"))

def upload_data_to_s3(filepath):
    """Upload raw dataset to S3"""

    s3.upload_file(filepath,S3_BUCKET,S3_DATA_KEY)
    print("✅ File uploaded to S3")


def load_data_from_s3():
    """Download raw dataset from S3."""
    
    import pandas as pd
    obj = s3.get_object(Bucket=S3_BUCKET, Key=S3_DATA_KEY)
    df  = pd.read_csv(obj["Body"])
    print(f"✅ Loaded data from S3: {df.shape}")
    return df

def upload_model_to_s3(obj, filename: str):
    """Serialize object with joblib and upload to S3."""

    buffer = io.BytesIO()
    joblib.dump(obj, buffer)   # write to buffer
    buffer.seek(0)

    s3.put_object(
        Bucket=S3_BUCKET,
        Key=S3_CHURN_MODEL_PREFIX + filename,
        Body=buffer.getvalue())

    print(f"✅ {filename} → s3://{S3_BUCKET}/{S3_CHURN_MODEL_PREFIX}{filename}")

def download_model_from_s3(filename: str):
    """Download and deserialize a joblib file from S3."""

    response = s3.get_object(
        Bucket=S3_BUCKET,
        Key=S3_CHURN_MODEL_PREFIX + filename)

    buffer = io.BytesIO(response["Body"].read())
    return joblib.load(buffer)


def load_tflite_from_s3(filename: str):
    """Load TFLite model directly from S3 into memory."""

    s3_key = S3_XRAY_MODEL_PREFIX + filename

    try:
        obj = s3.get_object(Bucket=S3_BUCKET, Key=s3_key)
        model_bytes = obj["Body"].read()

        interpreter = Interpreter(model_content=model_bytes)
        interpreter.allocate_tensors()

        print("✅ X-Ray Model Loaded")
        return interpreter

    except Exception as e:
        raise RuntimeError(f"Failed to load model from S3: {e}")
    
    



