from decorators import json_response
from ppars.apps.core.models import News
from pytz import timezone


@json_response
def ajax_ez_news(request):
    ajax_response = [{'title': news.title, 'message': news.message,
                      'created': news.created.astimezone(timezone('US/Eastern')).strftime("%m/%d/%y %I:%M:%S%p")}
                     for news in News.objects.filter(category='EZ').order_by('-created')]
    return ajax_response