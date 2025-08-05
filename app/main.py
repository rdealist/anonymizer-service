# app/main.py
import oss2
import uuid
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR

from .anonymizer import DicomAnonymizer
from .config import settings

# Initialize FastAPI app
app = FastAPI(
    title="DICOM Anonymizer Service",
    description="An API to anonymize DICOM files and upload them to Aliyun OSS.",
    version="1.0.0"
)

# Initialize Aliyun OSS Bucket
try:
    auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
    bucket = oss2.Bucket(auth, settings.OSS_ENDPOINT, settings.OSS_BUCKET_NAME)
except Exception as e:
    # This is a critical failure, the app shouldn't start.
    raise RuntimeError(f"Failed to initialize Aliyun OSS bucket: {e}")


@app.post("/api/v1/anonymize")
async def anonymize_dicom_file(
    profile: str = Form("default"),
    file: UploadFile = File(...)
):
    """
    Anonymizes a DICOM file based on a specified profile and uploads it to OSS.
    """
    if not file.filename.endswith(('.dcm', '.DCM')):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only DICOM files (.dcm) are accepted."
        )

    try:
        # Read file content into memory
        file_bytes = await file.read()

        # Initialize anonymizer with the selected profile
        anonymizer = DicomAnonymizer(profile_name=profile)

        # Perform anonymization and get the result as an in-memory bytes buffer
        anonymized_file_buffer = anonymizer.anonymize_and_save_to_bytes(file_bytes)

    except ValueError as e:
        # Catches errors from DicomAnonymizer (e.g., invalid DICOM, bad profile)
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Catch any other unexpected errors during anonymization
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal error occurred during file processing: {e}"
        )

    try:
        # Generate a unique object key for OSS
        oss_key = f"anonymized/{uuid.uuid4()}.dcm"

        # Upload the in-memory buffer to OSS
        bucket.put_object(oss_key, anonymized_file_buffer)

        # Construct the full OSS URL
        oss_url = f"{settings.OSS_ENDPOINT.replace('https://', f'https://{settings.OSS_BUCKET_NAME}.')}/{oss_key}"

    except oss2.exceptions.OssError as e:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file to OSS: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during OSS upload: {e}"
        )

    # Build the success response
    response_data = {
        "success": True,
        "message": "File anonymized and uploaded successfully.",
        "data": {
            "originalFilename": file.filename,
            "ossUrl": oss_url,
            "ossKey": oss_key
        }
    }

    return JSONResponse(status_code=HTTP_200_OK, content=response_data)

@app.get("/")
def read_root():
    return {"message": "Welcome to the DICOM Anonymizer Service. Use the /api/v1/anonymize endpoint to process files."}
