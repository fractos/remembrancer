variable "aws_region" {
  description = "Home AWS region for Remembrancer to run within."
}

variable "iam_user_name" {
  description = "Name for the remembrancer IAM user (default is \"remembrancer\")."
  default     = "remembrancer"
}

variable "kms_key_alias" {
  description = "The alias that the key will be known as (default is \"remembrancer\")."
  default     = "remembrancer"
}

variable "kms_key_description" {
  description = "Description for the AWS KMS master key that remembrancer will use."
  default     = "Remembrancer master key."
}

variable "kms_key_deletion_window_in_days" {
  description = "Number of days that key deletion will be scheduled for (7 to 30 days, default 7)."
  default     = 7
}

variable "iam_group_name" {
  description = "Name of the IAM group that the remembrancer user will belong to (default is \"remembrancers\")."
  default     = "remembrancers"
}

variable "iam_group_membership_name" {
  description = "Name of the group membership tuple (default is \"remembrancer\")."
  default     = "remembrancer"
}
