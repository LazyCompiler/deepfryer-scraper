import * as cdk from "aws-cdk-lib";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as ecs from "aws-cdk-lib/aws-ecs";
import * as ecspatterns from "aws-cdk-lib/aws-ecs-patterns";
import * as events from "aws-cdk-lib/aws-events";
import * as logs from "aws-cdk-lib/aws-logs";
import { Construct } from "constructs";
import * as ecr from "aws-cdk-lib/aws-ecr";
import * as iam from "aws-cdk-lib/aws-iam";

export class CdkStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // The code that defines your stack goes here

    // example resource
    // const queue = new sqs.Queue(this, 'CdkQueue', {
    //   visibilityTimeout: cdk.Duration.seconds(300)
    // });

    // Get the VPC
    const vpc = ec2.Vpc.fromLookup(this, "DeepFryerVPC", {
      tags: {
        "aws:cloudformation:stack-name": "DeepfryerCoreCdkStack",
      },
    });

    // console.log(vpc);

    // // Create timestream database
    // const timestreamDatabase = new timestream.CfnDatabase(this, 'DeepFryerTimestreamDatabase', {
    //   databaseName: 'DeepFryerTimestreamDatabase',
    // });

    // Create an ECS cluster
    const cluster = new ecs.Cluster(this, "DeepFryerScraperCluster", {
      clusterName: "deepfryer-scraper-cluster",
      containerInsights: true,
      vpc: vpc,
    });

    // Create ECR repository
    const repository = new ecr.Repository(this, "DeepFryerScraperRepository", {
      repositoryName: "deepfryer-scraper-repository",
    });

    // Create container image from ECR repository
    const image = ecs.ContainerImage.fromEcrRepository(repository);

    const scheduledFargateTask = new ecspatterns.ScheduledFargateTask(
      this,
      "DeepFryerScraperTask",
      {
        vpc: vpc,
        subnetSelection: {
          subnetType: ec2.SubnetType.PUBLIC,
        },
        schedule: events.Schedule.cron({
          minute: "0",
          hour: "15",
          day: "*",
          month: "*",
        }),
        cluster: cluster,
        platformVersion: ecs.FargatePlatformVersion.LATEST,
        scheduledFargateTaskImageOptions: {
          logDriver: ecs.LogDrivers.awsLogs({
            streamPrefix: id,
            logRetention: logs.RetentionDays.THREE_MONTHS,
          }),
          image: image,
          environment: {
            APP_NAME: id,
          },
          memoryLimitMiB: 1024,
          cpu: 256,
        },
      }
    );

    // SQS recive message policy
    scheduledFargateTask.taskDefinition.addToTaskRolePolicy(
      new iam.PolicyStatement({
        actions: [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "timestream:WriteRecords",
          "timestream:DescribeEndpoints",
        ],
        resources: ["*"],
      })
    );
  }
}
