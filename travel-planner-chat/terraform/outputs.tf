output "website_url" {
  value = "https://${aws_cloudfront_distribution.demo.domain_name}"
}
output "frontend_bucket" { value = aws_s3_bucket.frontend.id }
output "code_bucket" { value = aws_s3_bucket.code.id }
output "distribution_id" { value = aws_cloudfront_distribution.demo.id }
output "instance_id" { value = aws_instance.backend.id }
output "backend_role_arn" { value = aws_iam_role.backend.arn }
