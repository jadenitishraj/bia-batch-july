# CI may manage demo infrastructure, but cannot assume or edit arbitrary IAM roles.
resource "aws_iam_role_policy" "deploy" {
  role = aws_iam_role.github.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["ec2:Describe*", "ssm:GetParameter", "sts:GetCallerIdentity"]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = ["ec2:CreateVpc", "ec2:DeleteVpc", "ec2:ModifyVpcAttribute",
          "ec2:CreateSubnet", "ec2:DeleteSubnet", "ec2:ModifySubnetAttribute",
          "ec2:CreateInternetGateway", "ec2:DeleteInternetGateway",
          "ec2:AttachInternetGateway", "ec2:DetachInternetGateway",
          "ec2:CreateRouteTable", "ec2:DeleteRouteTable", "ec2:CreateRoute", "ec2:DeleteRoute",
          "ec2:AssociateRouteTable", "ec2:DisassociateRouteTable", "ec2:ReplaceRouteTableAssociation",
          "ec2:CreateSecurityGroup", "ec2:DeleteSecurityGroup", "ec2:AuthorizeSecurityGroupIngress",
          "ec2:RevokeSecurityGroupIngress", "ec2:AuthorizeSecurityGroupEgress", "ec2:RevokeSecurityGroupEgress",
          "ec2:RunInstances", "ec2:TerminateInstances", "ec2:StartInstances", "ec2:StopInstances",
          "ec2:ModifyInstanceAttribute", "ec2:ModifyInstanceMetadataOptions", "ec2:ModifyInstanceCreditSpecification",
        "ec2:CreateTags", "ec2:DeleteTags", "ec2:RequestSpotInstances", "ec2:CancelSpotInstanceRequests"]
        Resource  = "*"
        Condition = { StringEquals = { "aws:RequestedRegion" = "us-east-1" } }
      },
      {
        Effect = "Allow"
        Action = ["s3:CreateBucket", "s3:DeleteBucket", "s3:GetBucket*", "s3:ListBucket*",
          "s3:PutBucket*", "s3:DeleteBucketPolicy", "s3:GetEncryptionConfiguration",
        "s3:PutEncryptionConfiguration", "s3:GetObject*", "s3:PutObject*", "s3:DeleteObject*"]
        Resource = ["arn:aws:s3:::travel-demo-*", "arn:aws:s3:::travel-demo-*/*"]
      },
      {
        Effect = "Allow"
        Action = ["cloudfront:CreateDistribution", "cloudfront:GetDistribution*", "cloudfront:UpdateDistribution",
          "cloudfront:DeleteDistribution", "cloudfront:ListTagsForResource", "cloudfront:TagResource",
          "cloudfront:UntagResource", "cloudfront:CreateInvalidation", "cloudfront:GetInvalidation",
          "cloudfront:ListCachePolicies", "cloudfront:GetCachePolicy", "cloudfront:CreateVpcOrigin",
          "cloudfront:GetVpcOrigin", "cloudfront:UpdateVpcOrigin", "cloudfront:DeleteVpcOrigin",
          "cloudfront:CreateOriginAccessControl", "cloudfront:GetOriginAccessControl",
        "cloudfront:UpdateOriginAccessControl", "cloudfront:DeleteOriginAccessControl"]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = ["iam:CreateRole", "iam:DeleteRole", "iam:GetRole", "iam:TagRole", "iam:UntagRole",
          "iam:PutRolePolicy", "iam:GetRolePolicy", "iam:DeleteRolePolicy", "iam:ListRolePolicies",
          "iam:ListAttachedRolePolicies", "iam:AttachRolePolicy", "iam:DetachRolePolicy",
          "iam:CreateInstanceProfile", "iam:DeleteInstanceProfile", "iam:GetInstanceProfile",
          "iam:TagInstanceProfile", "iam:UntagInstanceProfile", "iam:ListInstanceProfilesForRole",
        "iam:AddRoleToInstanceProfile", "iam:RemoveRoleFromInstanceProfile", "iam:PassRole"]
        Resource = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/travel-demo/*",
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:instance-profile/travel-demo/*"]
      },
      {
        Effect   = "Allow", Action = "iam:CreateServiceLinkedRole"
        Resource = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/aws-service-role/*"
      },
      {
        Effect = "Allow", Action = "ssm:SendCommand"
        Resource = ["arn:aws:ssm:us-east-1::document/AWS-RunShellScript",
        "arn:aws:ec2:us-east-1:${data.aws_caller_identity.current.account_id}:instance/*"]
      },
      {
        Effect   = "Allow", Action = ["ssm:GetCommandInvocation", "ssm:ListCommandInvocations"]
        Resource = "*"
      }
    ]
  })
}
