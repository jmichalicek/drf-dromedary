from rest_framework.renderers import JSONRenderer


class AddsFooRenderer(JSONRenderer):
    
    def render(
        self, data, accepted_media_type = None, renderer_context = None
    ):
        with_foo = {f"foo_{k}": v for k,v in data.items()}
        return super().render(with_foo, accepted_media_type, renderer_context) 
