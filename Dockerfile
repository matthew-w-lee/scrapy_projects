# As Scrapy runs on Python, I choose the official Python 3 Docker image.
FROM python:3
 
RUN mkdir /app
WORKDIR /app
 
# Copy the file from the local host to the filesystem of the container at the working directory.
COPY . /app
 
# Install Scrapy specified in requirements.txt.
RUN pip3 install --no-cache-dir -r requirements.txt
  
# Run the crawler when the container launches.
#CMD [ "python3", "./go-spider.py" ]