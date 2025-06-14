# Define custom function directory
ARG FUNCTION_DIR="/var/task/"

# Define package source
ARG BUILD_PACKAGE=pycaltime@git+https://github.com/pjd199/timesheet@main
#
# Create the build image 
#
FROM --platform=linux/x86_64 python:3.12.6-bookworm as build-image

# Include global arg in this stage of the build
ARG FUNCTION_DIR
RUN mkdir -p ${FUNCTION_DIR}

# Install aws-lambda-cpp build dependencies
RUN apt-get update && \
  apt-get install -y \
  g++ \
  make \
  cmake \
  unzip \
  libcurl4-openssl-dev

# Install awslambdaric and the project
ARG BUILD_PACKAGE
RUN pip install --target ${FUNCTION_DIR} awslambdaric ${BUILD_PACKAGE}

#
# Create the runtime image from the build image
#
FROM --platform=linux/x86_64 python:3.12.6-slim-bookworm

# Include global arg in this stage of the build
ARG FUNCTION_DIR
# Set working directory to function root directory
WORKDIR ${FUNCTION_DIR}

# Copy in the built dependencies
COPY --from=build-image ${FUNCTION_DIR} ${FUNCTION_DIR}

# Set entry point and lambda handler
ENTRYPOINT [ "/usr/local/bin/python", "-m", "awslambdaric" ]
CMD ["src.app.lambda_handler"]