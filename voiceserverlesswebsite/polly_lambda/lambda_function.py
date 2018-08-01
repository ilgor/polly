import boto3
import os
import urllib.parse
from contextlib import closing

polly = boto3.client('polly')
s3 = boto3.resource('s3')

def lambda_handler(event, context):
    output = os.environ['output']
    supported_languages = os.environ['supported_languages'].split(',')
    default_language = os.environ['default_language']
    polly_bucket = os.environ['polly_bucket']

    s3_bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')

    try:
        whole_filename, file_extension = os.path.splitext(key)
        filename = whole_filename.split("/")[-1]
        text = str(s3.Object(s3_bucket, key).get()['Body'].read(), 'utf-8')
        # Get the language file_name.lang.md or file_name.md
        language = filename.split(".")[-1]
        voice_language = language if language in supported_languages else default_language

        voice_id = os.environ[voice_language]

        response = polly.synthesize_speech(
            OutputFormat=output,
            Text=text,
            VoiceId=voice_id
        )

        polly_title = "{}.{}".format(filename, output)

        if "AudioStream" in response:
            with closing(response['AudioStream']) as stream:
                output_title = os.path.join("/tmp", polly_title)
                with open(output_title, "ab") as f:
                    f.write(stream.read())

        s3.Object(polly_bucket, polly_title).upload_file(os.path.join("/tmp", polly_title),ExtraArgs={'ACL':'public-read'})

    except Exception as e:
        print('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function'.format(key, s3_bucket))
        raise e
