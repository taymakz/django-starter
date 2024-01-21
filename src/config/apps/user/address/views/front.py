import graphene
from apps.user.address.models import UserAddresses
from graphene import ObjectType
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required
from project.enums import ResponseMessage


class UserAddressesType(DjangoObjectType):
    class Meta:
        model = UserAddresses
        fields = (
            "id",
            "receiver_name",
            "receiver_family",
            "receiver_phone",
            "receiver_national_code",
            "receiver_province",
            "receiver_city",
            "receiver_postal_code",
            "receiver_address",
        )


class UserAddressQuery(ObjectType):
    user_address_list = graphene.List(UserAddressesType)
    user_address_detail = graphene.Field(UserAddressesType, id=graphene.ID())

    @login_required
    @staticmethod
    def resolve_user_address_list(parent, info):
        return UserAddresses.objects.filter(is_delete=False, user=info.context.user)

    @login_required
    @staticmethod
    def resolve_user_address_detail(parent, info, **kwargs):
        id = kwargs["id"]
        if id and info.context.user:
            try:
                return UserAddresses.objects.get(
                    id=kwargs["id"], user=info.context.user
                )

            except UserAddresses.DoesNotExist:
                return None
            except Exception as e:
                return None
        return None


class UserAddressesInput(graphene.InputObjectType):
    receiver_name = graphene.String()
    receiver_family = graphene.String()
    receiver_phone = graphene.String()
    receiver_national_code = graphene.String()
    receiver_province = graphene.String()
    receiver_city = graphene.String()
    receiver_postal_code = graphene.String()
    receiver_address = graphene.String()


class AddressCreate(graphene.Mutation):
    address = graphene.Field(UserAddressesType)
    message = graphene.String(default_value=None)
    success = graphene.Boolean(default_value=False)

    class Arguments:
        input_data = graphene.Argument(UserAddressesInput)

    @login_required
    @staticmethod
    def mutate(self, info, input_data):
        try:
            address = UserAddresses.objects.create(
                receiver_name=input_data.receiver_name,
                receiver_family=input_data.receiver_family,
                receiver_phone=input_data.receiver_phone,
                receiver_national_code=input_data.receiver_national_code,
                receiver_province=input_data.receiver_province,
                receiver_city=input_data.receiver_city,
                receiver_postal_code=input_data.receiver_postal_code,
                receiver_address=input_data.receiver_address,
                user=info.context.user,
            )
            return AddressCreate(
                address=address,
                message=ResponseMessage.USER_PANEL_ADDRESS_ADDED_SUCCESSFULLY.value,
                success=True,
            )
        except Exception as e:
            return AddressUpdate(message=ResponseMessage.FAILED.value)


class AddressUpdate(graphene.Mutation):
    address = graphene.Field(UserAddressesType, default_value=None)
    message = graphene.String(default_value=None)
    success = graphene.Boolean(default_value=False)

    class Arguments:
        id = graphene.ID()
        input_data = graphene.Argument(UserAddressesInput)

    @login_required
    @staticmethod
    def mutate(self, info, id, input_data=None):
        try:
            address = UserAddresses.objects.get(id=id, user=info.context.user)
            if input_data:
                for field, value in input_data.items():
                    setattr(address, field, value)
            address.save()

            return AddressUpdate(
                address=address,
                message=ResponseMessage.USER_PANEL_ADDRESS_EDITED_SUCCESSFULLY.value,
                success=True,
            )
        except UserAddresses.DoesNotExist:
            return AddressUpdate(
                message=ResponseMessage.USER_PANEL_ADDRESS_NOT_FOUND.value
            )


class AddressDelete(graphene.Mutation):
    message = graphene.String(default_value=None)
    success = graphene.Boolean(default_value=False)

    class Arguments:
        id = graphene.ID()

    @login_required
    @staticmethod
    def mutate(self, info, id):
        try:
            address = UserAddresses.objects.get(id=id, user=info.context.user)
            address.delete()
            return AddressDelete(
                message=ResponseMessage.USER_PANEL_ADDRESS_REMOVED_SUCCESSFULLY.value,
                success=True,
            )
        except UserAddresses.DoesNotExist:
            return AddressUpdate(
                message=ResponseMessage.USER_PANEL_ADDRESS_NOT_FOUND.value
            )


class UserAddressMutation(graphene.ObjectType):
    user_address_create = AddressCreate.Field()
    user_address_update = AddressUpdate.Field()
    user_address_delete = AddressDelete.Field()
