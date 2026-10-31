resource "aws_iam_role" "backend" {
  name_prefix = "travel-demo-backend-"
  path        = "/travel-demo/"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow", Action = "sts:AssumeRole"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.backend.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy" "backend" {
  role = aws_iam_role.backend.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow", Action = "bedrock:InvokeModel"
        Resource = [
          "arn:aws:bedrock:${var.region}:${data.aws_caller_identity.current.account_id}:inference-profile/us.amazon.nova-2-lite-v1:0",
          "arn:aws:bedrock:*::foundation-model/amazon.nova-2-lite-v1:0"
        ]
      },
      { Effect = "Allow", Action = "s3:GetObject", Resource = "${aws_s3_bucket.code.arn}/*" }
    ]
  })
}

resource "aws_iam_instance_profile" "backend" {
  name_prefix = "travel-demo-backend-"
  path        = "/travel-demo/"
  role        = aws_iam_role.backend.name
}

resource "aws_instance" "backend" {
  ami                         = data.aws_ssm_parameter.ami.value
  instance_type               = var.instance_type
  subnet_id                   = aws_subnet.demo.id
  vpc_security_group_ids      = [aws_security_group.backend.id]
  associate_public_ip_address = true
  iam_instance_profile        = aws_iam_instance_profile.backend.name
  tags                        = { Name = "travel-demo-backend" }

  instance_market_options {
    market_type = "spot"
    spot_options {
      spot_instance_type             = "persistent"
      instance_interruption_behavior = "stop"
    }
  }
  credit_specification { cpu_credits = "standard" }
  metadata_options { http_tokens = "required" }
  root_block_device {
    volume_type           = "gp3"
    volume_size           = 8
    encrypted             = true
    delete_on_termination = true
  }
  user_data = templatefile("${path.module}/bootstrap.sh", {
    code_bucket = aws_s3_bucket.code.id
    region      = var.region
  })
  depends_on = [aws_s3_object.backend, aws_iam_role_policy.backend,
  aws_iam_role_policy_attachment.ssm, aws_route_table_association.demo]
}
