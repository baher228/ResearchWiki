async def parse_pdf(file: UploadFile = File(...)):
    try:
        content = await file.read()
        return {"filename": file.filename, "content": content.decode("utf-8")}
    except Exception as exc:
        logger.exception("Upload failed")
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {exc}",
        )