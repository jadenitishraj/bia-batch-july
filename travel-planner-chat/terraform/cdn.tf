resource "aws_cloudfront_origin_access_control" "frontend" {
  name                              = "travel-demo-s3"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_vpc_origin" "backend" {
  vpc_origin_endpoint_config {
    name                   = "travel-demo-api"
    arn                    = aws_instance.backend.arn
    http_port              = 80
    https_port             = 443
    origin_protocol_policy = "http-only"
    origin_ssl_protocols {
      items    = ["TLSv1.2"]
      quantity = 1
    }
  }
  depends_on = [aws_internet_gateway.demo]
}

data "aws_cloudfront_cache_policy" "static" { name = "Managed-CachingOptimized" }

resource "aws_cloudfront_distribution" "demo" {
  enabled             = true
  default_root_object = "index.html"
  price_class         = "PriceClass_100"
  comment             = "Temporary Travel Planner classroom demo"
  wait_for_deployment = true

  origin {
    origin_id                = "frontend"
    domain_name              = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend.id
  }
  origin {
    origin_id   = "backend"
    domain_name = aws_instance.backend.private_dns
    vpc_origin_config {
      vpc_origin_id            = aws_cloudfront_vpc_origin.backend.id
      origin_read_timeout      = 60
      origin_keepalive_timeout = 5
    }
  }
  default_cache_behavior {
    target_origin_id       = "frontend"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true
    cache_policy_id        = data.aws_cloudfront_cache_policy.static.id
  }
  ordered_cache_behavior {
    path_pattern           = "/api/*"
    target_origin_id       = "backend"
    viewer_protocol_policy = "https-only"
    allowed_methods        = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods         = ["GET", "HEAD"]
    min_ttl                = 0
    default_ttl            = 0
    max_ttl                = 0
    forwarded_values {
      query_string = false
      headers      = ["Authorization", "Content-Type"]
      cookies { forward = "none" }
    }
  }
  restrictions {
    geo_restriction { restriction_type = "none" }
  }
  viewer_certificate { cloudfront_default_certificate = true }
}
