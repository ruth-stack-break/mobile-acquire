from src.logger import AcquisitionLogger

logger = AcquisitionLogger(
    "acquisition.log"
)

logger.info(
    "Tool started"
)

logger.warn(
    "Sample warning"
)

logger.error(
    "Sample error"
)

print(
    "Log written successfully"
)