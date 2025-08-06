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
bucket = None
if not settings.DEV_MODE:
    try:
        auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
        bucket = oss2.Bucket(auth, settings.OSS_ENDPOINT, settings.OSS_BUCKET_NAME)
    except Exception as e:
        # This is a critical failure, the app shouldn't start.
        raise RuntimeError(f"Failed to initialize Aliyun OSS bucket: {e}")
else:
    print("⚠️  Running in development mode - OSS functionality disabled")


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

    # Generate a unique object key for OSS
    oss_key = f"anonymized/{uuid.uuid4()}.dcm"

    if settings.DEV_MODE:
        # In development mode, simulate OSS upload
        oss_url = f"https://dev-bucket.oss-cn-hangzhou.aliyuncs.com/{oss_key}"
        print(f"🔧 DEV MODE: Simulated upload to {oss_url}")
    else:
        try:
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

@app.get("/api/v1/profiles")
def get_anonymizer_profiles():
    """
    获取可用的脱敏配置列表
    """
    try:
        # 从配置文件中读取所有可用的配置
        import yaml
        with open(settings.PROFILES_PATH, "r", encoding="utf-8") as f:
            all_profiles = yaml.safe_load(f)

        if not all_profiles or 'profiles' not in all_profiles:
            return JSONResponse(
                status_code=HTTP_200_OK,
                content={
                    "success": True,
                    "profiles": ["default"],
                    "descriptions": {
                        "default": "默认脱敏配置"
                    }
                }
            )

        profiles = list(all_profiles['profiles'].keys())
        descriptions = {
            "default": "默认脱敏配置，移除所有患者身份信息",
            "research": "科研脱敏配置，保留部分医学信息用于研究"
        }

        return JSONResponse(
            status_code=HTTP_200_OK,
            content={
                "success": True,
                "profiles": profiles,
                "descriptions": descriptions
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": f"Failed to load profiles: {e}"
            }
        )
