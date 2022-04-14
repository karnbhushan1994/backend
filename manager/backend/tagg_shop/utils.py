from collections import Counter
from heapq import heappush, nlargest

from ..widget.models import Widget, WidgetType


def get_top_taggs():
    widget_types = []
    for w in Widget.objects.order_by("order").select_subclasses():
        if w.type in [WidgetType.APPLICATION_LINK, WidgetType.VIDEO_LINK]:
            widget_types.append(w.link_type)
        else:
            widget_types.append(w.type)
    h = []
    for widget_type, freq in Counter(widget_types).items():
        heappush(h, (freq, widget_type))
    return [x[1] for x in nlargest(5, h)]
