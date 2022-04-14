from asyncio.log import logger
import json
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action

from ..common.validator import check_is_valid_parameter
from .constants import TAGG_SCORE_ALLOTMENT
from .models import GameProfile, TaggUser, Feature, UserFeature
from .serializers import (
    GameProfileSerializer,
    FeatureSerializer,
    UserFeatureSerializer,
    UserFeatureCreateSerializer,
)
from .utils import (
    increase_tagg_score, 
    decrease_tagg_score, 
    TaggScoreNotSufficient,
    get_converted_coins
)


class GameProfileViewSet(ModelViewSet):

    permission_classes = [IsAuthenticated]
    serializer_class = GameProfileSerializer

    queryset = GameProfile.objects.all()
    http_method_names = ["patch", "get"]

    def partial_update(self, request, pk=None, *args, **kwargs):
        if pk == None:
            return Response(
                data="pk is required to update gamification profile", status=400
            )

        user = TaggUser.objects.get(id=pk)
        data = request.query_params
        response_key = "points_earned"

        # Required tagg score key
        if not check_is_valid_parameter("tagg_score_type", data):
            return Response(data="tagg_score_type is a required parameter", status=400)
        # Restrict only for profile/moment sharing

        tagg_score_type = data.get("tagg_score_type")

        if tagg_score_type == "MOMENT_SHARE" or tagg_score_type == "PROFILE_SHARE":
            increase_tagg_score(user, TAGG_SCORE_ALLOTMENT[data.get("tagg_score_type")])
        elif tagg_score_type == "MOMENT_POST":
            try:
                decrease_tagg_score(
                    user, TAGG_SCORE_ALLOTMENT[data.get("tagg_score_type")]
                )
            except TaggScoreNotSufficient:
                return Response(
                    "Not sufficient balance to update tagg score", status=400
                )
            response_key = "points_removed"

        return Response(
            data={response_key: TAGG_SCORE_ALLOTMENT[data.get("tagg_score_type")]},
            status=200,
        )

    @action(detail=False, methods=["patch"])
    def unwrap_reward(self, request, pk=None, *args, **kwargs):
        try:

            data = request.query_params

            if not check_is_valid_parameter("userId", data):
                logger.error("userId is a required parameter")
                return Response(data="userId is a required parameter", status=400)

            if not check_is_valid_parameter("reward_type", data):
                logger.error("reward_type is a required parameter")
                return Response(data="reward_type is a required parameter", status=400)

            user = TaggUser.objects.get(id=data.get("userId"))
            reward_type = data.get("reward_type")

            game_profile = GameProfile.objects.filter(tagg_user=user)[0]
            opened_rewards = list(set(json.loads(game_profile.rewards)))
            unopened_rewards = list(set(json.loads(game_profile.newRewardsReceived)))

            if reward_type in opened_rewards:
                logger.error("Reward already unwrapped")
                return Response(data="Reward already unwrapped", status=200)

            elif reward_type not in unopened_rewards:
                logger.error("Reward not earned")
                return Response(data="Reward not earned", status=200)

            # Remove reward_type from newRewardsReceived and add to rewards
            elif reward_type in unopened_rewards:
                opened_rewards.append(reward_type)
                game_profile.rewards = json.dumps(opened_rewards)
                game_profile.save()

                new_rewards = [item for item in unopened_rewards if item != reward_type]
                game_profile.newRewardsReceived = json.dumps(new_rewards)
                game_profile.save()
                return Response(data="Successfully unwrapped reward", status=200)
            else:
                return Response(
                    data="Something went wrong while unwrapping reward", status=500
                )

        except Exception as err:
            logger.error("Something went wrong while unwrapping reward")
            return Response(
                data="Something went wrong while unwrapping reward", status=500
            )

    def retrieve(self, request, pk=None, *args, **kwargs):
        if pk == None:
            return Response(data="pk is required for GET", status=400)

        if not TaggUser.objects.filter(id=pk).exists():
            return Response(data="User does not exist", status=400)
        user = TaggUser.objects.get(id=pk)
        game_profile = GameProfile.objects.filter(tagg_user=user).first()
        result = GameProfileSerializer(game_profile).data
        if request.user == user:
            # send conversion from tagg coin to USD is logged in user
            # is looking at his/her own game profile
            result['coin_to_usd'] = get_converted_coins(result['tagg_score'])
        return Response(result, status=200)


class FeatureViewSet(ModelViewSet):

    permission_classes = [IsAuthenticated]
    serializer_class = FeatureSerializer

    queryset = Feature.objects.filter(active=True)
    http_method_names = ["get"]

    def retrieve(self, request, pk=None, *args, **kwargs):
        if pk == None:
            return Response(data="pk is required to GET Feature", status=400)

        feature = Feature.objects.filter(id=pk, active=True).first()
        if not feature:
            return Response(data="Feature does not exist", status=404)

        return Response(FeatureSerializer(feature).data, status=200)

    def list(self, request, *args, **kwargs):
        user = request.user
        features = self.get_queryset()
        for feature in features:
            if UserFeature.objects.filter(user=user, feature=feature):
                # UserFeature object exists meaning feature is unlocked for this user
                feature.unlocked = True
        return Response(FeatureSerializer(features, many=True).data, status=200)

    @action(detail=True, methods=["get"])
    def sufficient_balance(self, request, pk):
        user = request.user
        feature = Feature.objects.filter(id=pk).first()
        if not feature:
            return Response(data="Feature does not exist", status=404)

        game_profile = GameProfile.objects.filter(tagg_user=user).first()
        if not game_profile:
            return Response(data="GameProfile does not exist", status=404)

        if game_profile.tagg_score < feature.tagg_score_price:
            return Response(data="Not sufficient tagg score", status=400)
        return Response("Sufficent tagg score", status=200)


class UserFeatureViewSet(ModelViewSet):

    permission_classes = [IsAuthenticated]
    serializer_class = UserFeatureSerializer

    queryset = UserFeature.objects.filter(active=True)
    http_method_names = ["get", "post"]

    def retrieve(self, request, pk=None, *args, **kwargs):
        if pk == None:
            return Response(data="pk is required to GET User Feature", status=400)

        user_feature = UserFeature.objects.filter(id=pk, active=True).first()
        if not user_feature:
            return Response(data="User feature does not exist", status=404)

        return Response(UserFeatureSerializer(user_feature).data, status=200)

    def list(self, request, *args, **kwargs):
        result = self.get_queryset().filter(user=request.user)
        return Response(UserFeatureSerializer(result, many=True).data, status=200)

    def create(self, request, *args, **kwargs):
        """
        Creates UserFeature object
        Args:
            request.data['feature']: <id_of_feature>
        Returns:
            - "Feature does not exist" if feature object doesn't exits
            - "GameProfile does not exit", if user doesn't have a game profile
            - "Not sufficient tagg score", if user doesn't have sufficient tagg score to
                unlock this feature
            - Serialized data of user_feature object, with status 201
            - Serailizer errors if serializer can't validate fields doesn't get validated
        """
        data = request.data.copy()
        data["user"] = request.user.id
        data["active"] = True

        feature = Feature.objects.filter(id=data.get("feature")).first()
        if not feature:
            return Response(data="Feature does not exist", status=404)

        game_profile = GameProfile.objects.filter(tagg_user=request.user).first()
        if not game_profile:
            return Response(data="GameProfile does not exist", status=404)

        if game_profile.tagg_score < feature.tagg_score_price:
            return Response(data="Not sufficient tagg score", status=400)

        serializer = UserFeatureCreateSerializer(data=data)
        if serializer.is_valid():

            user_feature = serializer.save()

            # deduct feature price from tagg score
            game_profile.tagg_score -= user_feature.feature.tagg_score_price
            game_profile.save()

            return Response(UserFeatureSerializer(user_feature).data, status=201)
        return Response(serializer.errors, status=400)
