from pathlib import Path

from rest_framework import serializers


class ProcessingJobUploadSerializer(serializers.Serializer):
    file = serializers.FileField(max_length=255)

    def validate_file(self, uploaded_file):
        extension = Path(uploaded_file.name).suffix.lower()

        if extension not in {'.csv', '.json'}:
            raise serializers.ValidationError('Envie um arquivo CSV ou JSON.')

        if uploaded_file.size > 1024 * 1024:
            raise serializers.ValidationError('O arquivo deve ter no máximo 1 MiB.')

        return uploaded_file
