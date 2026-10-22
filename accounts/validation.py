from rest_framework import serializers


def validate_company_resource(user, resource, field_name):
    if (
        user
        and user.is_authenticated
        and user.tipo_usuario != 'admin'
        and (
            not user.empresa_id
            or resource.empresa_id != user.empresa_id
        )
    ):
        raise serializers.ValidationError({
            field_name: 'O recurso deve pertencer à sua empresa.'
        })


def validate_equipment_resource(user, equipamento, field_name='equipamento'):
    if equipamento is None:
        return
    validate_company_resource(user, equipamento, field_name)


def validate_sensor_resource(user, sensor, field_name='sensor'):
    if sensor is None:
        return
    validate_company_resource(user, sensor.equipamento, field_name)
