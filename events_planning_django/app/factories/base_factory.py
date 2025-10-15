from django.db import models


class BaseFactory:

    model = None

    def __init__(self, **overrides):

        self.overrides = overrides

    def make(self, **overrides):
        data = self._get_defaults()
        merged = {**data, **self.overrides, **overrides}
        
        return merged

    def create(self, **overrides):
        data = self.make(**overrides)
        instance = self.model.objects.create(**data)
        
        return instance

    def seed(self, count=1, **overrides):
        instances = []
        for _ in range(count):
            instance = self.create(**overrides)
            instances.append(instance)

        return instances

    def _get_defaults(self, **kwargs):
        raise NotImplementedError("Subclasses must implement _get_defaults()")
