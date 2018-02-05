provider "aws" {
  region = "${var.aws_region}"
}

terraform {
  backend "s3" {
    bucket = ""                  # fill with the name of the bucket for your remote state
    key    = "terraform.tfstate" # fill with the name of the key within that bucket
    region = ""                  # fill with your home AWS region
  }
}

resource "aws_iam_user" "remembrancer" {
  name = "${var.iam_user_name}"
}

resource "aws_iam_access_key" "remembrancer" {
  user = "${aws_iam_user.remembrancer.name}"
}

resource "aws_group" "remembrancers" {
  name = "${var.iam_group_name}"
}

resource "aws_iam_group_membership" "remembrancer" {
  name = "${var.iam_group_membership_name}"

  users = [
    "${aws_iam_user.remembrancer.name}",
  ]

  group = "${aws_iam_group.remembrancers.name}"
}

resource "aws_iam_group_policy" "remembrancers" {
  name  = "${var.iam_group_policy_name}"
  group = "${aws_iam_group.remembrancers.name}"

  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "kms:Decrypt",
                "kms:DescribeKey"
            ],
            "Resource": [
                "${aws_kms_key.remembrancer.arn}"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "ssm:PutParameter",
                "ssm:GetParameters"
            ],
            "Resource": [
                "*"
            ]
        }
    ]
}
EOF
}

data "aws_caller_identity" "current" {}

resource "aws_kms_key" "remembrancer" {
  description             = "${var.kms_key_description}"
  deletion_window_in_days = "${var.kms_key_deletion_window_in_days}"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "Enable IAM User Permissions",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
      },
      "Action": "kms:*",
      "Resource": "*"
    },
    {
      "Sid": "Allow use of the key",
      "Effect": "Allow",
      "Principal": {
        "AWS": [
          "${aws_iam_user.remembrancer.arn}"
        ]
      },
      "Action": [
        "kms:Encrypt",
        "kms:Decrypt",
        "kms:ReEncrypt*",
        "kms:GenerateDataKey*",
        "kms:DescribeKey"
      ],
      "Resource": "*"
    },
    {
      "Sid": "Allow attachment of persistent resources",
      "Effect": "Allow",
      "Principal": {
        "AWS": [
          "${aws_iam_user.remembrancer.arn}"
        ]
      },
      "Action": [
        "kms:CreateGrant",
        "kms:ListGrants",
        "kms:RevokeGrant"
      ],
      "Resource": "*",
      "Condition": {
        "Bool": {
          "kms:GrantIsForAWSResource": "true"
        }
      }
    }
  ]
}
EOF
}

resource "aws_kms_alias" "remembrancer" {
  name          = "alias/${var.kms_key_alias}"
  target_key_id = "${aws_kms_key.remembrancer.key_id}"
}
