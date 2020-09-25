import boto3
import os
import re


class Namespace:

    def __init__(self):
        dynamodb = boto3.resource("dynamodb")
        namespace_table_name = os.getenv("namespace_table_name")
        self.table = dynamodb.Table(namespace_table_name)


    def is_namespace_name_valid(self, namespace_name):
        if namespace_name is None:
            return False
        return re.match("[a-z0-9]([-a-z0-9]*[a-z0-9])?", namespace_name) # Namespace names must conform to the DNS Label RFC-1123 specification


    def get_all_namespaces(self, requesting_user):
        namespaces = self.table.scan()["Items"]
        if requesting_user is None:
            return namespaces
        else:
            return list(filter(lambda namespace: namespace["isPublic"] or requesting_user in namespace["administrators"], namespaces))


    def get_namespace(self, namespace_name):
        response = self.table.get_item(
            Key={
                "namespaceName": namespace_name
            }
        )
        if "Item" in response:
            return response["Item"]
        raise Exception


    def create_namespace(self, namespace_name, isPublic, administrators, status):
        self.table.put_item(
            Item={
                "namespaceName": namespace_name,
                "administrators": administrators,
                "isPublic": isPublic,
                "currentState": status
            },
            ConditionExpression=boto3.dynamodb.conditions.Attr("namespaceName").not_exists()
        )


    def update_namespace(self, namespace_name, isPublic, administrators):
        self.table.update_item(
            Key={
                "namespaceName": namespace_name
            },
            UpdateExpression="SET administrators = :administrators, isPublic = :isPublic",
            ExpressionAttributeValues={
                ":administrators": administrators,
                ":isPublic": isPublic
            },
            ConditionExpression=boto3.dynamodb.conditions.Attr("namespaceName").exists()
        )


    def update_namespace_status(self, namespace_name, status):
        self.table.update_item(
            Key={
                "namespaceName": namespace_name
            },
            UpdateExpression="SET currentState = :state",
            ExpressionAttributeValues={
                ":state": status
            },
            ConditionExpression=boto3.dynamodb.conditions.Attr("namespaceName").exists()
        )


    def delete(self, namespace_name):
        self.table.delete_item(
        Key={
            "namespaceName": namespace_name
        }
    )