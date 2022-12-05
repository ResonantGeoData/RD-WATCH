from rest_framework import serializers

from rdwatch.models import HyperParameters, lookups


class HyperParametersSerializer(serializers.ModelSerializer):
    performer = serializers.CharField(help_text="The team short-code")

    def validate_performer(self, value: str) -> lookups.Performer:
        try:
            return lookups.Performer.objects.get(slug=value.upper())
        except lookups.Performer.DoesNotExist:
            raise serializers.ValidationError(f"Invalid performer '{value}'")

    class Meta:
        model = HyperParameters
        fields = "__all__"
        extra_kwargs = {"parameters": {"default": dict}}
