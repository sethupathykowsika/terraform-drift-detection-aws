terraform {
  backend "s3" {
    bucket         = "my-driftdetection"
    key            = "drift-detection/terraform.tfstate"
    region         = "us-east-2"
    dynamodb_table = "terraform-drift"
    encrypt        = true
  }
}
