from inbox.services import NotificationService
from likes.api.serializers import (
    LikeSerializer,
    LikeSerializerForCreate,
    LikeSerializerForCancel,
)
from likes.models import Like
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utils.decorators import required_params


class LikeViewSet(viewsets.GenericViewSet):
    queryset = Like.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = LikeSerializerForCreate

    @required_params(method='POST', params=['content_type', 'object_id'])
    def create(self, request, *args, **kwargs):
        serializer = LikeSerializerForCreate(
            data=request.data,
            context={'request': request},
        )
        if not serializer.is_valid():
            return Response({
                'message': 'Please check input',
                'errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)
        #instance = serializer.save()
        #这里改为直接调用get_or_create(),是为了解决用户可能连续两次发送like create请求的情况
        instance, created = serializer.get_or_create()
        if created:
            NotificationService.send_like_notification(instance)
        return Response(
            LikeSerializer(instance).data,
            status=status.HTTP_201_CREATED,
        )
    '''
    这里使用POST方法而不是DELETE，是因为DELETE方法需要基于已经创建的like_id才能进行
    url设计类似：DELETE /api/likes/<id>/, 如果是这样就必须等待like create请求结束
    www服务器返回给前端created like_id才行，这样会导致不好的用户体验，所以我们使用
    POST方法去发送cancel请求，url设计类似：/api/likes/cancel/
    '''
    @action(methods=['POST'], detail=False)
    @required_params(method='POST', params=['content_type', 'object_id'])
    def cancel(self, request, *args, **kwargs):
        serializer = LikeSerializerForCancel(
            data=request.data,
            context={'request': request},
        )
        if not serializer.is_valid():
            return Response({
                'message': 'Please check input',
                'errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)
        serializer.cancel()
        return Response({'success': True}, status=status.HTTP_200_OK)