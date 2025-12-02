DROP TABLE IF EXISTS `access_control_audit`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `access_control_audit` (
  `audit_id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `action` varchar(100) NOT NULL,
  `target_user_id` int DEFAULT NULL,
  `permission_id` int DEFAULT NULL,
  `details` json DEFAULT NULL,
  `ip_address` varchar(45) DEFAULT NULL,
  `user_agent` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`audit_id`),
  KEY `target_user_id` (`target_user_id`),
  KEY `permission_id` (`permission_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_action` (`action`),
  KEY `idx_created_at` (`created_at`),
  CONSTRAINT `access_control_audit_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE SET NULL,
  CONSTRAINT `access_control_audit_ibfk_2` FOREIGN KEY (`target_user_id`) REFERENCES `users` (`user_id`) ON DELETE SET NULL,
  CONSTRAINT `access_control_audit_ibfk_3` FOREIGN KEY (`permission_id`) REFERENCES `permissions` (`permission_id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `access_control_audit`
--

LOCK TABLES `access_control_audit` WRITE;
/*!40000 ALTER TABLE `access_control_audit` DISABLE KEYS */;
INSERT INTO `access_control_audit` VALUES (1,1,'user_updated',2,NULL,'{\"changes\": {\"role\": {\"to\": \"client\", \"from\": \"client\"}, \"phone\": \"0777140803\", \"status\": {\"to\": \"active\", \"from\": \"pending\"}, \"full_name\": \"Ilham Safeek\"}}','127.0.0.1',NULL,'2025-11-16 14:14:58');
/*!40000 ALTER TABLE `access_control_audit` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `activity_logs`
--

DROP TABLE IF EXISTS `activity_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `activity_logs` (
  `log_id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `activity_type` varchar(100) NOT NULL,
  `activity_description` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`log_id`),
  KEY `idx_user_id` (`user_id`),
  CONSTRAINT `activity_logs_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `activity_logs`
--

LOCK TABLES `activity_logs` WRITE;
/*!40000 ALTER TABLE `activity_logs` DISABLE KEYS */;
/*!40000 ALTER TABLE `activity_logs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ad_campaigns`
--

DROP TABLE IF EXISTS `ad_campaigns`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ad_campaigns` (
  `campaign_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `created_by` int NOT NULL,
  `campaign_name` varchar(255) NOT NULL,
  `platform` varchar(50) NOT NULL,
  `objective` varchar(100) DEFAULT NULL,
  `budget` decimal(12,2) DEFAULT NULL,
  `start_date` date DEFAULT NULL,
  `end_date` date DEFAULT NULL,
  `status` enum('draft','active','paused','completed') DEFAULT 'draft',
  `target_audience` json DEFAULT NULL,
  `placement_settings` json DEFAULT NULL,
  `bidding_strategy` varchar(100) DEFAULT NULL,
  `external_campaign_id` varchar(255) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`campaign_id`),
  KEY `created_by` (`created_by`),
  KEY `idx_client_platform` (`client_id`,`platform`),
  CONSTRAINT `ad_campaigns_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `ad_campaigns_ibfk_2` FOREIGN KEY (`created_by`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ad_campaigns`
--

LOCK TABLES `ad_campaigns` WRITE;
/*!40000 ALTER TABLE `ad_campaigns` DISABLE KEYS */;
INSERT INTO `ad_campaigns` VALUES (1,17,1,'Testing Campaign ','google','brand_awareness',1000.00,'2025-11-15',NULL,'active','{}','{}',NULL,'google_1_1763228938','2025-11-15 17:48:46');
/*!40000 ALTER TABLE `ad_campaigns` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ad_performance`
--

DROP TABLE IF EXISTS `ad_performance`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ad_performance` (
  `performance_id` int NOT NULL AUTO_INCREMENT,
  `ad_id` int NOT NULL,
  `metric_date` date NOT NULL,
  `impressions` int DEFAULT '0',
  `clicks` int DEFAULT '0',
  `ctr` decimal(5,2) DEFAULT NULL,
  `cpc` decimal(10,2) DEFAULT NULL,
  `spend` decimal(12,2) DEFAULT NULL,
  `conversions` int DEFAULT '0',
  `roas` decimal(10,2) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`performance_id`),
  UNIQUE KEY `unique_ad_date` (`ad_id`,`metric_date`),
  CONSTRAINT `ad_performance_ibfk_1` FOREIGN KEY (`ad_id`) REFERENCES `ads` (`ad_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ad_performance`
--

LOCK TABLES `ad_performance` WRITE;
/*!40000 ALTER TABLE `ad_performance` DISABLE KEYS */;
/*!40000 ALTER TABLE `ad_performance` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ads`
--

DROP TABLE IF EXISTS `ads`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ads` (
  `ad_id` int NOT NULL AUTO_INCREMENT,
  `campaign_id` int NOT NULL,
  `ad_name` varchar(255) NOT NULL,
  `ad_format` varchar(50) DEFAULT NULL,
  `primary_text` text,
  `headline` varchar(255) DEFAULT NULL,
  `description` text,
  `media_urls` json DEFAULT NULL,
  `ai_generated` tinyint(1) DEFAULT '0',
  `status` enum('active','paused') DEFAULT 'active',
  `external_ad_id` varchar(255) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`ad_id`),
  KEY `campaign_id` (`campaign_id`),
  CONSTRAINT `ads_ibfk_1` FOREIGN KEY (`campaign_id`) REFERENCES `ad_campaigns` (`campaign_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ads`
--

LOCK TABLES `ads` WRITE;
/*!40000 ALTER TABLE `ads` DISABLE KEYS */;
/*!40000 ALTER TABLE `ads` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ai_ad_suggestions`
--

DROP TABLE IF EXISTS `ai_ad_suggestions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ai_ad_suggestions` (
  `suggestion_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `campaign_id` int DEFAULT NULL,
  `audience_segments` json DEFAULT NULL,
  `platform_recommendations` json DEFAULT NULL,
  `ad_copy_suggestions` json DEFAULT NULL,
  `budget_recommendations` json DEFAULT NULL,
  `forecasted_metrics` json DEFAULT NULL,
  `status` enum('pending','accepted','rejected') DEFAULT 'pending',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`suggestion_id`),
  KEY `campaign_id` (`campaign_id`),
  KEY `idx_client_id` (`client_id`),
  CONSTRAINT `ai_ad_suggestions_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `ai_ad_suggestions_ibfk_2` FOREIGN KEY (`campaign_id`) REFERENCES `ad_campaigns` (`campaign_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ai_ad_suggestions`
--

LOCK TABLES `ai_ad_suggestions` WRITE;
/*!40000 ALTER TABLE `ai_ad_suggestions` DISABLE KEYS */;
/*!40000 ALTER TABLE `ai_ad_suggestions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `analytics_alerts`
--

DROP TABLE IF EXISTS `analytics_alerts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `analytics_alerts` (
  `alert_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `alert_type` varchar(50) NOT NULL,
  `metric_name` varchar(100) NOT NULL,
  `message` text,
  `current_value` decimal(12,2) DEFAULT NULL,
  `previous_value` decimal(12,2) DEFAULT NULL,
  `threshold_value` decimal(12,2) DEFAULT NULL,
  `recommendation` text,
  `status` varchar(20) DEFAULT 'active',
  `acknowledged_by` int DEFAULT NULL,
  `acknowledged_at` timestamp NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `resolved_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`alert_id`),
  KEY `acknowledged_by` (`acknowledged_by`),
  KEY `idx_client_status` (`client_id`,`status`),
  KEY `idx_created` (`created_at`),
  CONSTRAINT `analytics_alerts_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `analytics_alerts_ibfk_2` FOREIGN KEY (`acknowledged_by`) REFERENCES `users` (`user_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `analytics_alerts`
--

LOCK TABLES `analytics_alerts` WRITE;
/*!40000 ALTER TABLE `analytics_alerts` DISABLE KEYS */;
/*!40000 ALTER TABLE `analytics_alerts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `analytics_campaign`
--

DROP TABLE IF EXISTS `analytics_campaign`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `analytics_campaign` (
  `campaign_analytics_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `campaign_id` int DEFAULT NULL,
  `campaign_name` varchar(255) DEFAULT NULL,
  `campaign_type` enum('ads','email','social','seo') NOT NULL,
  `metric_date` date NOT NULL,
  `impressions` int DEFAULT '0',
  `clicks` int DEFAULT '0',
  `conversions` int DEFAULT '0',
  `spend` decimal(12,2) DEFAULT '0.00',
  `ctr` decimal(5,2) DEFAULT NULL,
  `roas` decimal(10,2) DEFAULT NULL,
  `engagement_rate` decimal(5,2) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`campaign_analytics_id`),
  KEY `idx_client_campaign` (`client_id`,`campaign_type`),
  KEY `idx_metric_date` (`metric_date`),
  CONSTRAINT `analytics_campaign_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `analytics_campaign`
--

LOCK TABLES `analytics_campaign` WRITE;
/*!40000 ALTER TABLE `analytics_campaign` DISABLE KEYS */;
/*!40000 ALTER TABLE `analytics_campaign` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `analytics_overview`
--

DROP TABLE IF EXISTS `analytics_overview`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `analytics_overview` (
  `overview_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `metric_date` date NOT NULL,
  `total_ad_spend` decimal(12,2) DEFAULT '0.00',
  `total_impressions` int DEFAULT '0',
  `total_clicks` int DEFAULT '0',
  `total_conversions` int DEFAULT '0',
  `total_roas` decimal(10,2) DEFAULT NULL,
  `website_visits` int DEFAULT '0',
  `organic_traffic` int DEFAULT '0',
  `social_engagement` int DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`overview_id`),
  UNIQUE KEY `unique_client_date` (`client_id`,`metric_date`),
  CONSTRAINT `analytics_overview_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `analytics_overview`
--

LOCK TABLES `analytics_overview` WRITE;
/*!40000 ALTER TABLE `analytics_overview` DISABLE KEYS */;
INSERT INTO `analytics_overview` VALUES (1,17,'2025-11-16',0.00,0,0,0,0.00,0,0,0,'2025-11-15 23:02:18');
/*!40000 ALTER TABLE `analytics_overview` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `analytics_weekly`
--

DROP TABLE IF EXISTS `analytics_weekly`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `analytics_weekly` (
  `weekly_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `week_start_date` date NOT NULL,
  `week_end_date` date NOT NULL,
  `total_ad_spend` decimal(12,2) DEFAULT '0.00',
  `total_impressions` int DEFAULT '0',
  `total_clicks` int DEFAULT '0',
  `total_conversions` int DEFAULT '0',
  `avg_ctr` decimal(5,2) DEFAULT NULL,
  `avg_roas` decimal(10,2) DEFAULT NULL,
  `website_visits` int DEFAULT '0',
  `avg_bounce_rate` decimal(5,2) DEFAULT NULL,
  `organic_traffic` int DEFAULT '0',
  `social_engagement` int DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`weekly_id`),
  UNIQUE KEY `unique_client_week` (`client_id`,`week_start_date`),
  KEY `idx_week_dates` (`week_start_date`,`week_end_date`),
  CONSTRAINT `analytics_weekly_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `analytics_weekly`
--

LOCK TABLES `analytics_weekly` WRITE;
/*!40000 ALTER TABLE `analytics_weekly` DISABLE KEYS */;
/*!40000 ALTER TABLE `analytics_weekly` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `api_integrations`
--

DROP TABLE IF EXISTS `api_integrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `api_integrations` (
  `integration_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `service_name` varchar(100) NOT NULL,
  `credentials_encrypted` text,
  `status` enum('active','inactive') DEFAULT 'active',
  `last_sync` timestamp NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`integration_id`),
  KEY `idx_client_service` (`client_id`,`service_name`),
  CONSTRAINT `api_integrations_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `api_integrations`
--

LOCK TABLES `api_integrations` WRITE;
/*!40000 ALTER TABLE `api_integrations` DISABLE KEYS */;
/*!40000 ALTER TABLE `api_integrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `audience_segments`
--

DROP TABLE IF EXISTS `audience_segments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `audience_segments` (
  `segment_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `segment_name` varchar(255) NOT NULL,
  `description` text,
  `platform` varchar(50) DEFAULT NULL,
  `segment_criteria` json NOT NULL,
  `estimated_size` int DEFAULT NULL,
  `created_by` int NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`segment_id`),
  KEY `created_by` (`created_by`),
  KEY `idx_client_id` (`client_id`),
  CONSTRAINT `audience_segments_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `audience_segments_ibfk_2` FOREIGN KEY (`created_by`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `audience_segments`
--

LOCK TABLES `audience_segments` WRITE;
/*!40000 ALTER TABLE `audience_segments` DISABLE KEYS */;
INSERT INTO `audience_segments` VALUES (7,17,'Testing','Uploaded segment with 1 contacts','all','{\"columns\": [\"name\", \"email\", \"phone\"], \"upload_type\": \"csv\", \"uploaded_at\": \"2025-11-14T21:12:23.772Z\", \"total_contacts\": 1}',1,1,'2025-11-14 21:12:23','2025-11-14 21:12:23'),(8,17,'Email','Uploaded segment with 1 contacts','email','{\"columns\": [\"name\", \"email\", \"phone\"], \"upload_type\": \"csv\", \"uploaded_at\": \"2025-11-14T21:50:33.083Z\", \"total_contacts\": 1}',1,1,'2025-11-14 21:50:33','2025-11-14 21:50:33');
/*!40000 ALTER TABLE `audience_segments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `backlinks`
--

DROP TABLE IF EXISTS `backlinks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `backlinks` (
  `backlink_id` int NOT NULL AUTO_INCREMENT,
  `seo_project_id` int NOT NULL,
  `source_url` varchar(500) NOT NULL,
  `target_url` varchar(500) NOT NULL,
  `anchor_text` varchar(255) DEFAULT NULL,
  `status` enum('active','lost') DEFAULT 'active',
  `outreach_email` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`backlink_id`),
  KEY `seo_project_id` (`seo_project_id`),
  CONSTRAINT `backlinks_ibfk_1` FOREIGN KEY (`seo_project_id`) REFERENCES `seo_projects` (`seo_project_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `backlinks`
--

LOCK TABLES `backlinks` WRITE;
/*!40000 ALTER TABLE `backlinks` DISABLE KEYS */;
INSERT INTO `backlinks` VALUES (1,1,'https://apmi.lk','https://hashnate.com/','hashnate','active','{\"subject\": \"Partnership Opportunity - Quality Backlink Exchange\", \"body\": \"Hi,\\n\\nI hope this email finds you well. I\'m reaching out from https://hashnate.com/ regarding a potential collaboration.\\n\\nWe\'ve been following your work at https://apmi.lk and believe there could be mutual value in connecting our audiences.\\n\\nWould you be interested in discussing how we might work together?\\n\\nBest regards\"}','2025-11-15 15:25:21');
/*!40000 ALTER TABLE `backlinks` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `campaign_analytics`
--

DROP TABLE IF EXISTS `campaign_analytics`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `campaign_analytics` (
  `campaign_analytics_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `platform` varchar(50) NOT NULL,
  `campaign_id` varchar(255) NOT NULL,
  `campaign_name` varchar(500) DEFAULT NULL,
  `metric_date` date NOT NULL,
  `impressions` int DEFAULT '0',
  `clicks` int DEFAULT '0',
  `conversions` int DEFAULT '0',
  `spend` decimal(12,2) DEFAULT '0.00',
  `revenue` decimal(12,2) DEFAULT '0.00',
  `ctr` decimal(5,2) DEFAULT '0.00',
  `cpc` decimal(8,2) DEFAULT '0.00',
  `roas` decimal(8,2) DEFAULT '0.00',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`campaign_analytics_id`),
  UNIQUE KEY `unique_campaign_date` (`client_id`,`platform`,`campaign_id`,`metric_date`),
  KEY `idx_client_platform` (`client_id`,`platform`),
  KEY `idx_date` (`metric_date`),
  CONSTRAINT `campaign_analytics_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `campaign_analytics`
--

LOCK TABLES `campaign_analytics` WRITE;
/*!40000 ALTER TABLE `campaign_analytics` DISABLE KEYS */;
/*!40000 ALTER TABLE `campaign_analytics` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `chatbot_conversations`
--

DROP TABLE IF EXISTS `chatbot_conversations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `chatbot_conversations` (
  `conversation_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `session_id` varchar(255) NOT NULL,
  `platform` varchar(50) DEFAULT 'web',
  `status` enum('active','closed') DEFAULT 'active',
  `lead_qualified` tinyint(1) DEFAULT '0',
  `qualification_data` json DEFAULT NULL,
  `started_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`conversation_id`),
  KEY `user_id` (`user_id`),
  KEY `idx_session_id` (`session_id`),
  CONSTRAINT `chatbot_conversations_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `chatbot_conversations`
--

LOCK TABLES `chatbot_conversations` WRITE;
/*!40000 ALTER TABLE `chatbot_conversations` DISABLE KEYS */;
INSERT INTO `chatbot_conversations` VALUES (2,NULL,'5115003b-2a74-4499-983d-897fb064e76e','web','active',0,NULL,'2025-11-15 23:47:40'),(3,NULL,'1e09bba9-36e6-4ef9-926f-a2aa2df532d2','web','active',0,NULL,'2025-11-15 23:48:23'),(4,NULL,'0db45f07-2c30-457c-b842-d3bdd357131c','web','active',0,NULL,'2025-11-15 23:53:40'),(5,1,'9fbae68a-131e-4de6-aabc-ca0867ac7db4','web','active',1,'{\"score\": 90, \"intent\": \"purchase\", \"urgency\": \"high\", \"is_qualified\": true, \"key_interests\": [\"Professional package\", \"Immediate start\"], \"suggested_action\": \"Follow up with a welcome email and confirm the start of the service\", \"budget_indication\": \"none\"}','2025-11-15 23:57:40');
/*!40000 ALTER TABLE `chatbot_conversations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `chatbot_messages`
--

DROP TABLE IF EXISTS `chatbot_messages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `chatbot_messages` (
  `message_id` int NOT NULL AUTO_INCREMENT,
  `conversation_id` int NOT NULL,
  `sender_type` enum('user','bot') NOT NULL,
  `message_text` text NOT NULL,
  `sentiment` varchar(20) DEFAULT 'neutral',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`message_id`),
  KEY `conversation_id` (`conversation_id`),
  CONSTRAINT `chatbot_messages_ibfk_1` FOREIGN KEY (`conversation_id`) REFERENCES `chatbot_conversations` (`conversation_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=24 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `chatbot_messages`
--

LOCK TABLES `chatbot_messages` WRITE;
/*!40000 ALTER TABLE `chatbot_messages` DISABLE KEYS */;
INSERT INTO `chatbot_messages` VALUES (1,2,'user','Tell me about my package','neutral','2025-11-15 23:47:45'),(2,2,'bot','Of course! However, I\'ll need a bit more information to provide accurate details. Could you please specify which package you\'re currently subscribed to: is it the Basic, Professional, or Enterprise package?','neutral','2025-11-15 23:47:56'),(3,3,'user','Show my campaign performance','neutral','2025-11-15 23:48:27'),(4,3,'bot','I\'m sorry for any confusion, but as an AI text-based assistant, I don\'t have the capability to display visual data or access your personal campaign performance. However, I can guide you on how to view it on the PanvelIQ platform. \n\n1. Sign in to your PanvelIQ account.\n2. Navigate to the Analytics Dashboard on the main menu.\n3. Here, you can view all your campaign performance metrics across different channels. \n\nRemember, you can filter by date, campaign, or platform to get a more detailed view. If you need further assistance or have any other questions, feel free to ask!','neutral','2025-11-15 23:48:37'),(5,4,'user','Hi','neutral','2025-11-15 23:53:51'),(6,4,'bot','Hello! How can I assist you with PanvelIQ\'s digital marketing intelligence platform today?','neutral','2025-11-15 23:54:08'),(7,5,'bot','Hello! I\'m your PanvelIQ Assistant. How can I help you today?','positive','2025-11-15 23:57:40'),(8,5,'user','I need help with marketing strategy','neutral','2025-11-15 23:58:00'),(9,5,'bot','Of course, I\'d be glad to assist you with that! Could you please provide me with some more details about your business? Information like your target audience, current marketing efforts, and your specific goals will help me give you the most tailored advice.','positive','2025-11-15 23:58:09'),(10,5,'user','my name is ilham.','neutral','2025-11-15 23:58:35'),(11,5,'bot','Nice to meet you, Ilham! How can I assist you with your marketing strategy today?','positive','2025-11-15 23:58:40'),(12,5,'user','Hi! I\'m looking for help with digital marketing for my small business.','neutral','2025-11-16 00:00:35'),(13,5,'bot','Hi Ilham! I\'d be happy to help you with digital marketing for your small business. Can you tell me more about the nature of your business and your specific goals? Also, do you have any current marketing efforts in place? This will help me guide you to the most appropriate PanvelIQ services for your needs.','positive','2025-11-16 00:00:43'),(14,5,'user','I\'m launching a new product next month and need help with social media ads. \nThis is really urgent!','neutral','2025-11-16 00:01:10'),(15,5,'bot','I understand the urgency, Ilham. To ensure a successful product launch, our Ad Strategy Engine and Social Media Management services will be particularly useful. \n\nThe Ad Strategy Engine will help you create and manage intelligent ad campaigns while Social Media Management will enable you to schedule posts across multiple platforms simultaneously, saving you time and effort.\n\nWe also have the Creative Media Studio to assist in creating compelling images, videos, or animations for your ads. \n\nWould you like to know more about these services? Or perhaps you\'re interested in a specific package?','positive','2025-11-16 00:01:19'),(16,5,'user','I have around $600 per month to spend. I want to focus on Instagram and Facebook. \nI need this set up ASAP because the launch is in 3 weeks!','neutral','2025-11-16 00:01:59'),(17,5,'bot','Great, Ilham! With a budget of $600 per month, our Professional package would be a perfect fit. It includes advanced features and priority support, which will be crucial for your upcoming product launch. \n\nIn this package, you\'ll have access to our Social Media Management service to manage your Instagram and Facebook posts efficiently. Plus, the Ad Strategy Engine will assist you in setting up and managing intelligent ad campaigns on these platforms. \n\nTo get started as quickly as possible, I suggest that you sign up for the Professional package now. We can get the setup process initiated right away to ensure everything is prepared for your product launch in 3 weeks. How does that sound?','positive','2025-11-16 00:02:12'),(18,5,'user','Yes! That sounds perfect. How soon can we start?','positive','2025-11-16 00:02:56'),(19,5,'bot','Fantastic, Ilham! We can start right away. As soon as you complete the sign-up process for the Professional package, our team will begin setting up your account and services. \n\nIf you need any assistance during the sign-up process or have any other questions, feel free to ask. I\'m here to help!','positive','2025-11-16 00:03:04'),(20,5,'user','how can I contact someone from your company?','neutral','2025-11-16 00:17:17'),(21,5,'bot','Absolutely, Ilham! You can reach out to our team through the following channels:\n\n1. Email: support@panveliq.com\n2. Phone: +1 123 456 7890\n3. Live chat: You can find this on our website.\n\nOur team is available Monday to Friday, 9 am - 5 pm ET. If you reach out outside these hours, we\'ll get back to you as quickly as possible the next business day.','positive','2025-11-16 00:17:25'),(22,5,'user','thanks bye. please close the chat.','neutral','2025-11-16 00:17:51'),(23,5,'bot','You\'re welcome, Ilham! If you have any more questions in the future, don\'t hesitate to reach out. Best of luck with your product launch! Goodbye for now. [Chat Closed]','positive','2025-11-16 00:18:01');
/*!40000 ALTER TABLE `chatbot_messages` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `client_ad_platforms`
--

DROP TABLE IF EXISTS `client_ad_platforms`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `client_ad_platforms` (
  `connection_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `platform` varchar(50) NOT NULL,
  `account_id` varchar(255) DEFAULT NULL,
  `access_token` text,
  `refresh_token` text,
  `token_expires_at` timestamp NULL DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT '1',
  `last_sync_at` timestamp NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`connection_id`),
  UNIQUE KEY `unique_client_platform` (`client_id`,`platform`),
  KEY `idx_client` (`client_id`),
  KEY `idx_active` (`is_active`),
  CONSTRAINT `client_ad_platforms_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `client_ad_platforms`
--

LOCK TABLES `client_ad_platforms` WRITE;
/*!40000 ALTER TABLE `client_ad_platforms` DISABLE KEYS */;
/*!40000 ALTER TABLE `client_ad_platforms` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `client_profiles`
--

DROP TABLE IF EXISTS `client_profiles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `client_profiles` (
  `profile_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `business_name` varchar(255) DEFAULT NULL,
  `business_type` varchar(100) DEFAULT NULL,
  `website_url` varchar(500) DEFAULT NULL,
  `current_budget` decimal(12,2) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `meta_ad_account_id` varchar(255) DEFAULT NULL,
  `google_ads_account_id` varchar(255) DEFAULT NULL,
  `linkedin_ads_account_id` varchar(255) DEFAULT NULL,
  `google_analytics_property_id` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`profile_id`),
  UNIQUE KEY `client_id` (`client_id`),
  CONSTRAINT `client_profiles_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `client_profiles`
--

LOCK TABLES `client_profiles` WRITE;
/*!40000 ALTER TABLE `client_profiles` DISABLE KEYS */;
/*!40000 ALTER TABLE `client_profiles` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `client_subscriptions`
--

DROP TABLE IF EXISTS `client_subscriptions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `client_subscriptions` (
  `subscription_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `package_id` int NOT NULL,
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  `status` enum('active','expired','cancelled') DEFAULT 'active',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`subscription_id`),
  KEY `package_id` (`package_id`),
  KEY `idx_client_id` (`client_id`),
  CONSTRAINT `client_subscriptions_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `client_subscriptions_ibfk_2` FOREIGN KEY (`package_id`) REFERENCES `packages` (`package_id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `client_subscriptions`
--

LOCK TABLES `client_subscriptions` WRITE;
/*!40000 ALTER TABLE `client_subscriptions` DISABLE KEYS */;
INSERT INTO `client_subscriptions` VALUES (1,17,5,'2025-11-14','2025-12-14','active','2025-11-14 14:50:15'),(2,19,5,'2025-11-17','2025-12-17','active','2025-11-17 06:38:52');
/*!40000 ALTER TABLE `client_subscriptions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `competitor_analyses`
--

DROP TABLE IF EXISTS `competitor_analyses`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `competitor_analyses` (
  `analysis_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `primary_domain` varchar(500) DEFAULT NULL,
  `competitor_domains` json DEFAULT NULL,
  `analysis_data` json DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`analysis_id`),
  KEY `idx_client` (`client_id`),
  KEY `idx_created` (`created_at`),
  CONSTRAINT `competitor_analyses_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `competitor_analyses`
--

LOCK TABLES `competitor_analyses` WRITE;
/*!40000 ALTER TABLE `competitor_analyses` DISABLE KEYS */;
/*!40000 ALTER TABLE `competitor_analyses` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `content_library`
--

DROP TABLE IF EXISTS `content_library`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `content_library` (
  `content_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `created_by` int NOT NULL,
  `platform` varchar(50) DEFAULT NULL,
  `content_type` enum('text','image','video','carousel') NOT NULL,
  `title` varchar(255) DEFAULT NULL,
  `content_text` text,
  `hashtags` json DEFAULT NULL,
  `cta_text` varchar(255) DEFAULT NULL,
  `ai_generated` tinyint(1) DEFAULT '0',
  `optimization_score` decimal(5,2) DEFAULT NULL,
  `status` enum('draft','approved','published') DEFAULT 'draft',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`content_id`),
  KEY `created_by` (`created_by`),
  KEY `idx_client_id` (`client_id`),
  KEY `idx_platform` (`platform`),
  CONSTRAINT `content_library_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `content_library_ibfk_2` FOREIGN KEY (`created_by`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `content_library`
--

LOCK TABLES `content_library` WRITE;
/*!40000 ALTER TABLE `content_library` DISABLE KEYS */;
INSERT INTO `content_library` VALUES (1,17,1,'instagram','video','Unleash the Power of Your Business with Royal Super Oil!','Meet the power of ultimate performance - Royal Super Oil. Engineered for efficiency, designed to save your small business time and money. Don’t just run your business, make it excel! Visit royalsuper.us now to learn more.','[\"RoyalSuperOil\", \"oilindustry\", \"energysector\", \"advertising\", \"digitalmarketing\", \"onlinepromotion\", \"websitetraffic\", \"oilexploration\", \"naturalresources\", \"businessgrowth\", \"brandawareness\", \"onlinestrategy\", \"industryinsights\", \"trendingbusiness\", \"ecommerce\"]','Boost your business performance today! Visit royalsuper.us now.',1,100.00,'draft','2025-11-15 08:10:34');
/*!40000 ALTER TABLE `content_library` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `conversion_funnels`
--

DROP TABLE IF EXISTS `conversion_funnels`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `conversion_funnels` (
  `funnel_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `funnel_name` varchar(255) NOT NULL,
  `funnel_stages` json NOT NULL,
  `drop_off_analysis` json DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`funnel_id`),
  KEY `client_id` (`client_id`),
  CONSTRAINT `conversion_funnels_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `conversion_funnels`
--

LOCK TABLES `conversion_funnels` WRITE;
/*!40000 ALTER TABLE `conversion_funnels` DISABLE KEYS */;
/*!40000 ALTER TABLE `conversion_funnels` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `conversion_funnels_data`
--

DROP TABLE IF EXISTS `conversion_funnels_data`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `conversion_funnels_data` (
  `funnel_data_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `funnel_name` varchar(255) NOT NULL,
  `metric_date` date NOT NULL,
  `step_1_visitors` int DEFAULT '0',
  `step_2_engaged` int DEFAULT '0',
  `step_3_cart` int DEFAULT '0',
  `step_4_checkout` int DEFAULT '0',
  `step_5_completed` int DEFAULT '0',
  `total_revenue` decimal(12,2) DEFAULT '0.00',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`funnel_data_id`),
  UNIQUE KEY `unique_funnel_date` (`client_id`,`funnel_name`,`metric_date`),
  KEY `idx_client_date` (`client_id`,`metric_date`),
  CONSTRAINT `conversion_funnels_data_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `conversion_funnels_data`
--

LOCK TABLES `conversion_funnels_data` WRITE;
/*!40000 ALTER TABLE `conversion_funnels_data` DISABLE KEYS */;
/*!40000 ALTER TABLE `conversion_funnels_data` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `email_campaigns`
--

DROP TABLE IF EXISTS `email_campaigns`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `email_campaigns` (
  `email_campaign_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `created_by` int NOT NULL,
  `campaign_name` varchar(255) NOT NULL,
  `subject_line` varchar(255) NOT NULL,
  `email_body` text,
  `segment_criteria` json DEFAULT NULL,
  `schedule_type` enum('immediate','scheduled') DEFAULT 'scheduled',
  `scheduled_at` timestamp NULL DEFAULT NULL,
  `status` enum('draft','scheduled','sent') DEFAULT 'draft',
  `total_recipients` int DEFAULT '0',
  `opened_count` int DEFAULT '0',
  `clicked_count` int DEFAULT '0',
  `is_ab_test` tinyint(1) DEFAULT '0',
  `ab_test_config` json DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`email_campaign_id`),
  KEY `created_by` (`created_by`),
  KEY `idx_client_id` (`client_id`),
  CONSTRAINT `email_campaigns_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `email_campaigns_ibfk_2` FOREIGN KEY (`created_by`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `email_campaigns`
--

LOCK TABLES `email_campaigns` WRITE;
/*!40000 ALTER TABLE `email_campaigns` DISABLE KEYS */;
INSERT INTO `email_campaigns` VALUES (1,17,1,'Testing Mail','Boost Your Business Profit With Our Exclusive Offer!','<p>Dear SME Owner,</p><p> </p><p>We understand the challenges you face in growing your business. That\'s why we have crafted an exclusive offer designed to boost your profits and streamline your operations.</p><p> </p><p>For a limited time, we\'re offering a 20% discount on our all-in-one business solution package. This package includes advanced tools for inventory management, sales tracking, customer relationship management, and more.</p><p> </p><p>With these tools at your disposal, you can optimize your processes, make data-driven decisions, and focus more on what matters most - growing your business.</p><p> </p><p>Don\'t miss this opportunity to invest in your business\' future. Click the button below to claim your discount and start your journey to higher profits today.</p><p> </p><p>Best regards,</p><p> </p><p>Your Success Partner</p>','{}','immediate',NULL,'sent',0,0,0,0,NULL,'2025-11-14 21:51:33'),(2,17,1,'Hi Test','Unlock Your Business Potential: Increase Sales Now!','<p>Dear SME Owner,</p><p>We understand the challenges you face in running your business. And one of the most significant of these challenges is increasing sales to meet your financial goals.</p><p>We are excited to introduce our proven strategies that have helped many businesses like yours increase their sales and improve their bottom line. </p><p>Our approach is unique - we don\'t just provide strategies, but we also work alongside you to implement these strategies and ensure they produce the desired results.</p><p>Click the button below to start your journey towards higher sales and a more sustainable business.</p><p>Best Regards,Your Name</p>','{}','immediate',NULL,'sent',0,0,0,0,NULL,'2025-11-14 22:00:23'),(3,17,1,'Welcome Test','Unlock the Future with Our Latest Tech Gadgets!','<p>\n\n</p><p>Hey there Tech Enthusiast,</p><p>\n</p><p>We know you love to stay ahead of the curve with the most innovative and futuristic tech gadgets. That\'s why we\'re thrilled to introduce our latest range of products that are sure to blow your mind!</p><p>\n</p><p>From smart home systems to wearables that monitor your health, we have something for every tech enthusiast. Our products are designed with you in mind, offering superior performance, innovative design, and the latest technology.</p><p>\n</p><p>But that\'s not all! For a limited time only, we\'re offering an exclusive discount on our newest products. But hurry, this offer won\'t last long!</p><p>\n</p><p>Ready to explore the future of technology? Click the button below to get started.</p><p>\n</p><p><a href=\"http://www.ourwebsite.com/new-products\" style=\"background-color:#FF0000;border:none;color:white;padding:15px 32px;text-align:center;text-decoration:none;display:inline-block;font-size:16px;margin:4px 2px;cursor:pointer;\">Discover Now</a></p><p>\n</p><p>Stay tech-obsessed,</p><p>\n</p><p>Your friends at [Your Company]</p><p>\n\n</p>','{}','immediate',NULL,'sent',0,0,0,0,NULL,'2025-11-14 22:02:43'),(4,17,1,'Hi','Unlock Tech Magic! Exclusive Deals Just for You!','<p>Hey there Tech Whizz,</p><p>We know you love to stay ahead of the curve, always exploring the latest gadgets and technologies. That\'s why we\'ve curated an exclusive collection of cutting-edge tech products just for you!</p><p>For a limited time, enjoy unbeatable deals on our top-selling items. From the latest smartphones and laptops to innovative home automation solutions, we\'ve got you covered.</p><p>Remember, these deals won\'t last forever. So, don\'t miss your chance to upgrade your tech arsenal and save big at the same time.</p><p>Ready to dive into our tech wonderland?</p><p><br></p><p>Stay Techy,</p><p>Your Friends at [Your Brand Name]</p>','{}','immediate',NULL,'sent',1,0,0,0,NULL,'2025-11-14 22:13:51'),(5,17,1,'Hi','Unlock Tech Magic! Exclusive Deals Just for You!','<p>Hey there Tech Whizz,</p><p>We know you love to stay ahead of the curve, always exploring the latest gadgets and technologies. That\'s why we\'ve curated an exclusive collection of cutting-edge tech products just for you!</p><p>For a limited time, enjoy unbeatable deals on our top-selling items. From the latest smartphones and laptops to innovative home automation solutions, we\'ve got you covered.</p><p>Remember, these deals won\'t last forever. So, don\'t miss your chance to upgrade your tech arsenal and save big at the same time.</p><p>Ready to dive into our tech wonderland?</p><p><br></p><p>Stay Techy,</p><p>Your Friends at [Your Brand Name]</p>','{}','immediate',NULL,'sent',0,0,0,0,NULL,'2025-11-14 22:14:22');
/*!40000 ALTER TABLE `email_campaigns` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `employee_assignments`
--

DROP TABLE IF EXISTS `employee_assignments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `employee_assignments` (
  `assignment_id` int NOT NULL AUTO_INCREMENT,
  `employee_id` int NOT NULL,
  `client_id` int NOT NULL,
  `assigned_by` int NOT NULL,
  `assigned_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`assignment_id`),
  UNIQUE KEY `unique_assignment` (`employee_id`,`client_id`),
  KEY `client_id` (`client_id`),
  KEY `assigned_by` (`assigned_by`),
  CONSTRAINT `employee_assignments_ibfk_1` FOREIGN KEY (`employee_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `employee_assignments_ibfk_2` FOREIGN KEY (`client_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `employee_assignments_ibfk_3` FOREIGN KEY (`assigned_by`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `employee_assignments`
--

LOCK TABLES `employee_assignments` WRITE;
/*!40000 ALTER TABLE `employee_assignments` DISABLE KEYS */;
INSERT INTO `employee_assignments` VALUES (1,3,17,1,'2025-11-14 14:56:14');
/*!40000 ALTER TABLE `employee_assignments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `financial_transactions`
--

DROP TABLE IF EXISTS `financial_transactions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `financial_transactions` (
  `transaction_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `transaction_type` enum('revenue','expense') NOT NULL,
  `amount` decimal(12,2) NOT NULL,
  `description` text,
  `transaction_date` date NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`transaction_id`),
  KEY `idx_client_id` (`client_id`),
  KEY `idx_transaction_date` (`transaction_date`),
  CONSTRAINT `financial_transactions_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `financial_transactions`
--

LOCK TABLES `financial_transactions` WRITE;
/*!40000 ALTER TABLE `financial_transactions` DISABLE KEYS */;
INSERT INTO `financial_transactions` VALUES (1,17,'expense',1200.00,'Test','2025-11-17','2025-11-17 04:41:54');
/*!40000 ALTER TABLE `financial_transactions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `flow_executions`
--

DROP TABLE IF EXISTS `flow_executions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `flow_executions` (
  `execution_id` int NOT NULL AUTO_INCREMENT,
  `flow_id` int NOT NULL,
  `triggered_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `status` enum('success','failed') DEFAULT 'success',
  `error_message` text,
  PRIMARY KEY (`execution_id`),
  KEY `idx_flow_id` (`flow_id`),
  CONSTRAINT `flow_executions_ibfk_1` FOREIGN KEY (`flow_id`) REFERENCES `triggered_flows` (`flow_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `flow_executions`
--

LOCK TABLES `flow_executions` WRITE;
/*!40000 ALTER TABLE `flow_executions` DISABLE KEYS */;
/*!40000 ALTER TABLE `flow_executions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ga4_data`
--

DROP TABLE IF EXISTS `ga4_data`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ga4_data` (
  `ga4_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `property_id` varchar(255) DEFAULT NULL,
  `metric_date` date NOT NULL,
  `page_views` int DEFAULT '0',
  `unique_visitors` int DEFAULT '0',
  `avg_session_duration` decimal(10,2) DEFAULT NULL,
  `bounce_rate` decimal(5,2) DEFAULT NULL,
  `new_users` int DEFAULT '0',
  `returning_users` int DEFAULT '0',
  `conversion_events` int DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`ga4_id`),
  UNIQUE KEY `unique_client_property_date` (`client_id`,`property_id`,`metric_date`),
  KEY `idx_metric_date` (`metric_date`),
  CONSTRAINT `ga4_data_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ga4_data`
--

LOCK TABLES `ga4_data` WRITE;
/*!40000 ALTER TABLE `ga4_data` DISABLE KEYS */;
/*!40000 ALTER TABLE `ga4_data` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `heatmap_data`
--

DROP TABLE IF EXISTS `heatmap_data`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `heatmap_data` (
  `heatmap_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `page_url` varchar(500) NOT NULL,
  `element_selector` varchar(255) DEFAULT NULL,
  `click_x` int DEFAULT NULL,
  `click_y` int DEFAULT NULL,
  `interaction_type` enum('click','scroll','hover') NOT NULL,
  `session_id` varchar(255) DEFAULT NULL,
  `tracked_date` date NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`heatmap_id`),
  KEY `idx_client_page` (`client_id`,`page_url`(255)),
  KEY `idx_tracked_date` (`tracked_date`),
  CONSTRAINT `heatmap_data_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `heatmap_data`
--

LOCK TABLES `heatmap_data` WRITE;
/*!40000 ALTER TABLE `heatmap_data` DISABLE KEYS */;
/*!40000 ALTER TABLE `heatmap_data` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `keyword_movement`
--

DROP TABLE IF EXISTS `keyword_movement`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `keyword_movement` (
  `movement_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `keyword` varchar(255) NOT NULL,
  `previous_position` int DEFAULT NULL,
  `current_position` int DEFAULT NULL,
  `position_change` int DEFAULT NULL,
  `search_volume` int DEFAULT NULL,
  `tracked_date` date NOT NULL,
  `change_percentage` decimal(5,2) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`movement_id`),
  KEY `idx_client_keyword` (`client_id`,`keyword`),
  KEY `idx_tracked_date` (`tracked_date`),
  CONSTRAINT `keyword_movement_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `keyword_movement`
--

LOCK TABLES `keyword_movement` WRITE;
/*!40000 ALTER TABLE `keyword_movement` DISABLE KEYS */;
/*!40000 ALTER TABLE `keyword_movement` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `keyword_rankings`
--

DROP TABLE IF EXISTS `keyword_rankings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `keyword_rankings` (
  `ranking_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `keyword` varchar(255) NOT NULL,
  `search_engine` varchar(50) DEFAULT 'google',
  `current_position` int DEFAULT NULL,
  `previous_position` int DEFAULT NULL,
  `position_change` int DEFAULT NULL,
  `search_volume` int DEFAULT '0',
  `metric_date` date NOT NULL,
  `landing_page_url` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`ranking_id`),
  UNIQUE KEY `unique_keyword_date` (`client_id`,`keyword`,`search_engine`,`metric_date`),
  KEY `idx_client_date` (`client_id`,`metric_date`),
  KEY `idx_position` (`current_position`),
  CONSTRAINT `keyword_rankings_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `keyword_rankings`
--

LOCK TABLES `keyword_rankings` WRITE;
/*!40000 ALTER TABLE `keyword_rankings` DISABLE KEYS */;
/*!40000 ALTER TABLE `keyword_rankings` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `keyword_tracking`
--

DROP TABLE IF EXISTS `keyword_tracking`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `keyword_tracking` (
  `keyword_id` int NOT NULL AUTO_INCREMENT,
  `seo_project_id` int NOT NULL,
  `keyword` text NOT NULL,
  `search_volume` int DEFAULT NULL,
  `current_position` int DEFAULT NULL,
  `tracked_date` date NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`keyword_id`),
  KEY `seo_project_id` (`seo_project_id`),
  CONSTRAINT `keyword_tracking_ibfk_1` FOREIGN KEY (`seo_project_id`) REFERENCES `seo_projects` (`seo_project_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `keyword_tracking`
--

LOCK TABLES `keyword_tracking` WRITE;
/*!40000 ALTER TABLE `keyword_tracking` DISABLE KEYS */;
INSERT INTO `keyword_tracking` VALUES (1,1,'ERP',5466,81,'2025-11-15','2025-11-15 11:28:31'),(2,1,'Ilham',5918,51,'2025-11-15','2025-11-15 15:26:53'),(3,1,'ERP',1316,57,'2025-11-17','2025-11-17 04:48:28');
/*!40000 ALTER TABLE `keyword_tracking` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `media_assets`
--

DROP TABLE IF EXISTS `media_assets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `media_assets` (
  `asset_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `created_by` int NOT NULL,
  `asset_type` enum('image','video','animation','presentation') NOT NULL,
  `asset_name` varchar(255) NOT NULL,
  `file_url` varchar(500) NOT NULL,
  `ai_generated` tinyint(1) DEFAULT '0',
  `generation_type` varchar(100) DEFAULT NULL,
  `prompt_used` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`asset_id`),
  KEY `created_by` (`created_by`),
  KEY `idx_client_id` (`client_id`),
  CONSTRAINT `media_assets_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `media_assets_ibfk_2` FOREIGN KEY (`created_by`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `media_assets`
--

LOCK TABLES `media_assets` WRITE;
/*!40000 ALTER TABLE `media_assets` DISABLE KEYS */;
INSERT INTO `media_assets` VALUES (1,17,1,'image','DALL-E Image 1','https://oaidalleapiprodscus.blob.core.windows.net/private/org-2H0EcLMKzyY5ZRRu2x4RCa5F/user-UINOi1v0dJffUzMLFrxTetex/img-GR1nNZhtCgAvT03qRI7010lY.png?st=2025-11-15T07%3A49%3A38Z&se=2025-11-15T09%3A49%3A38Z&sp=r&sv=2024-08-04&sr=b&rscd=inline&rsct=image/png&skoid=8b33a531-2df9-46a3-bc02-d4b1430a422c&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2025-11-15T08%3A49%3A38Z&ske=2025-11-16T08%3A49%3A38Z&sks=b&skv=2024-08-04&sig=55ZYquZpdWxuJMzyaYQKTq09aZBy/VscVVfWVVutnR0%3D',1,'dall-e-3','11:11 Sale at Panvel','2025-11-15 08:49:38'),(4,17,1,'image','DALL-E Image 1','https://oaidalleapiprodscus.blob.core.windows.net/private/org-2H0EcLMKzyY5ZRRu2x4RCa5F/user-UINOi1v0dJffUzMLFrxTetex/img-4Ye95lIdOrokXQj672l99ZWQ.png?st=2025-11-15T15%3A28%3A48Z&se=2025-11-15T17%3A28%3A48Z&sp=r&sv=2024-08-04&sr=b&rscd=inline&rsct=image/png&skoid=f1dafa11-a0c2-4092-91d4-10981fbda051&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2025-11-15T15%3A26%3A56Z&ske=2025-11-16T15%3A26%3A56Z&sks=b&skv=2024-08-04&sig=WDt046QOrAZvFuR2piaIjvwzcK3fxh6ILlyJwyR8%2BH4%3D',1,'dall-e-3','Sale in hashnate Software Company','2025-11-15 16:28:48'),(5,17,1,'image','DALL-E Image 1','https://oaidalleapiprodscus.blob.core.windows.net/private/org-2H0EcLMKzyY5ZRRu2x4RCa5F/user-UINOi1v0dJffUzMLFrxTetex/img-ABixHf8mGuksF4ey9lVc10OS.png?st=2025-11-15T15%3A37%3A16Z&se=2025-11-15T17%3A37%3A16Z&sp=r&sv=2024-08-04&sr=b&rscd=inline&rsct=image/png&skoid=77e5a8ec-6bd1-4477-8afc-16703a64f029&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2025-11-15T16%3A29%3A13Z&ske=2025-11-16T16%3A29%3A13Z&sks=b&skv=2024-08-04&sig=VV3IXlx0g5AExzeow0YHxR2E3pa7hKr12CYcp3TOBMo%3D',1,'dall-e-3','Raneema Risnee Girl in a garden kitchen and his husband working with laptop in autumn season.','2025-11-15 16:37:16'),(6,17,1,'image','DALL-E Image 1','https://oaidalleapiprodscus.blob.core.windows.net/private/org-2H0EcLMKzyY5ZRRu2x4RCa5F/user-UINOi1v0dJffUzMLFrxTetex/img-ulKqClabN11YRszvTQE0Sqm9.png?st=2025-11-17T03%3A51%3A26Z&se=2025-11-17T05%3A51%3A26Z&sp=r&sv=2024-08-04&sr=b&rscd=inline&rsct=image/png&skoid=f1dafa11-a0c2-4092-91d4-10981fbda051&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2025-11-17T03%3A28%3A29Z&ske=2025-11-18T03%3A28%3A29Z&sks=b&skv=2024-08-04&sig=sji3xHf%2Bnpq1QtjlpB9qKvbTAgyi2UOQZmUsQNvYZwU%3D',1,'dall-e-3','Working at office with laptop in winter season with 4 team members. All are muslims','2025-11-17 04:51:26');
/*!40000 ALTER TABLE `media_assets` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `messages`
--

DROP TABLE IF EXISTS `messages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `messages` (
  `message_id` int NOT NULL AUTO_INCREMENT,
  `sender_id` int NOT NULL,
  `receiver_id` int NOT NULL,
  `subject` varchar(255) DEFAULT NULL,
  `message_body` text NOT NULL,
  `is_read` tinyint(1) DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`message_id`),
  KEY `sender_id` (`sender_id`),
  KEY `idx_receiver_id` (`receiver_id`),
  CONSTRAINT `messages_ibfk_1` FOREIGN KEY (`sender_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `messages_ibfk_2` FOREIGN KEY (`receiver_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `messages`
--

LOCK TABLES `messages` WRITE;
/*!40000 ALTER TABLE `messages` DISABLE KEYS */;
INSERT INTO `messages` VALUES (1,17,3,'Tst','Testing',0,'2025-11-17 08:50:00'),(2,17,1,'Admin test','testing',0,'2025-11-17 08:53:27');
/*!40000 ALTER TABLE `messages` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `notifications`
--

DROP TABLE IF EXISTS `notifications`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `notifications` (
  `notification_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `notification_type` varchar(100) NOT NULL,
  `title` varchar(255) NOT NULL,
  `message` text,
  `is_read` tinyint(1) DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`notification_id`),
  KEY `idx_user_id` (`user_id`),
  CONSTRAINT `notifications_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `notifications`
--

LOCK TABLES `notifications` WRITE;
/*!40000 ALTER TABLE `notifications` DISABLE KEYS */;
INSERT INTO `notifications` VALUES (1,3,'client_message','Testing msg','Message here',0,'2025-11-17 08:46:19');
/*!40000 ALTER TABLE `notifications` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `onboarding_sessions`
--

DROP TABLE IF EXISTS `onboarding_sessions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `onboarding_sessions` (
  `onboarding_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `selected_package_id` int DEFAULT NULL,
  `verification_data` json DEFAULT NULL,
  `verification_status` enum('pending','verified','rejected') DEFAULT 'pending',
  `discussion_notes` text,
  `verified_by` int DEFAULT NULL,
  `verified_at` timestamp NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`onboarding_id`),
  KEY `selected_package_id` (`selected_package_id`),
  KEY `verified_by` (`verified_by`),
  KEY `idx_user_id` (`user_id`),
  CONSTRAINT `onboarding_sessions_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `onboarding_sessions_ibfk_2` FOREIGN KEY (`selected_package_id`) REFERENCES `packages` (`package_id`),
  CONSTRAINT `onboarding_sessions_ibfk_3` FOREIGN KEY (`verified_by`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `onboarding_sessions`
--

LOCK TABLES `onboarding_sessions` WRITE;
/*!40000 ALTER TABLE `onboarding_sessions` DISABLE KEYS */;
INSERT INTO `onboarding_sessions` VALUES (1,17,5,'{\"website_url\": \"https://informake.com\", \"company_size\": \"1-10\", \"business_name\": \"Informake\", \"business_type\": \"saas\", \"monthly_budget\": 1000, \"marketing_goals\": \"Increase Website Awareness and Product Awareness\", \"current_challenges\": null}','verified',NULL,1,'2025-11-14 14:50:15','2025-11-14 13:43:12'),(2,19,5,NULL,'verified',NULL,1,'2025-11-17 06:38:52','2025-11-17 05:23:08'),(3,22,5,NULL,'pending',NULL,NULL,NULL,'2025-11-17 08:28:06'),(4,23,5,NULL,'pending',NULL,NULL,NULL,'2025-11-17 12:11:27');
/*!40000 ALTER TABLE `onboarding_sessions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `packages`
--

DROP TABLE IF EXISTS `packages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `packages` (
  `package_id` int NOT NULL AUTO_INCREMENT,
  `package_name` varchar(100) NOT NULL,
  `package_tier` enum('basic','professional','enterprise') NOT NULL,
  `description` text,
  `price` decimal(10,2) NOT NULL,
  `billing_cycle` enum('monthly','quarterly','yearly') NOT NULL,
  `features` json DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`package_id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `packages`
--

LOCK TABLES `packages` WRITE;
/*!40000 ALTER TABLE `packages` DISABLE KEYS */;
INSERT INTO `packages` VALUES (4,'Starter Plan','basic','Perfect for small businesses starting their digital marketing journey',499.00,'monthly','{\"feature_1\": \"Social Media Management (2 platforms)\", \"feature_2\": \"Basic SEO Optimization\", \"feature_3\": \"Email Marketing (up to 1,000 contacts)\", \"feature_4\": \"Content Creation (10 posts/month)\", \"feature_5\": \"Monthly Performance Report\", \"feature_6\": \"Email Support\", \"feature_7\": \"1 User Account\", \"feature_8\": \"Campaign Analytics Dashboard\"}',1,'2025-11-14 12:49:49'),(5,'Growth Plan','professional','Ideal for growing businesses ready to scale their marketing efforts',1299.00,'monthly','{\"feature1\": \"Social Media Management (5 platforms)\", \"feature2\": \"Advanced SEO with Keyword Research\", \"feature3\": \"Email Marketing (up to 5,000 contacts)\", \"feature4\": \"Content Creation (30 posts/month)\", \"feature5\": \"AI-Powered Content Suggestions\", \"feature6\": \"WhatsApp Campaign Management\", \"feature7\": \"Google Ads Management\", \"feature8\": \"Facebook/Instagram Ads\", \"feature9\": \"Weekly Performance Reports\", \"feature10\": \"Priority Email & Chat Support\", \"feature11\": \"Up to 3 User Accounts\", \"feature12\": \"A/B Testing for Campaigns\", \"feature13\": \"Competitor Analysis\"}',1,'2025-11-14 12:49:49'),(6,'Enterprise Plan','enterprise','Comprehensive solution for established businesses with advanced marketing needs',2999.00,'monthly','{\"feature1\": \"Unlimited Social Media Management\", \"feature2\": \"Enterprise SEO with Backlink Strategy\", \"feature3\": \"Email Marketing (unlimited contacts)\", \"feature4\": \"Unlimited Content Creation\", \"feature5\": \"AI-Powered Strategy Recommendations\", \"feature6\": \"WhatsApp + SMS Campaign Management\", \"feature7\": \"Multi-Channel Ad Management\", \"feature8\": \"Advanced Analytics & Predictive Insights\", \"feature9\": \"Creative Media Studio (AI Video/Image)\", \"feature10\": \"Real-time Performance Tracking\", \"feature11\": \"Dedicated Account Manager\", \"feature12\": \"24/7 Priority Support\", \"feature13\": \"Unlimited User Accounts\", \"feature14\": \"Custom Integrations\", \"feature15\": \"White-label Reporting\", \"feature16\": \"Quarterly Strategy Sessions\"}',1,'2025-11-14 12:49:49');
/*!40000 ALTER TABLE `packages` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `password_reset_tokens`
--

DROP TABLE IF EXISTS `password_reset_tokens`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `password_reset_tokens` (
  `token_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `reset_token` varchar(255) NOT NULL,
  `expires_at` timestamp NOT NULL,
  `is_used` tinyint(1) DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `used_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`token_id`),
  UNIQUE KEY `reset_token` (`reset_token`),
  KEY `idx_reset_token` (`reset_token`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_expires` (`expires_at`),
  CONSTRAINT `password_reset_tokens_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `password_reset_tokens`
--

LOCK TABLES `password_reset_tokens` WRITE;
/*!40000 ALTER TABLE `password_reset_tokens` DISABLE KEYS */;
/*!40000 ALTER TABLE `password_reset_tokens` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `performance_alerts`
--

DROP TABLE IF EXISTS `performance_alerts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `performance_alerts` (
  `alert_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `alert_type` varchar(100) NOT NULL,
  `title` varchar(255) NOT NULL,
  `description` text,
  `is_read` tinyint(1) DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`alert_id`),
  KEY `idx_client_id` (`client_id`),
  CONSTRAINT `performance_alerts_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `performance_alerts`
--

LOCK TABLES `performance_alerts` WRITE;
/*!40000 ALTER TABLE `performance_alerts` DISABLE KEYS */;
/*!40000 ALTER TABLE `performance_alerts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `performance_anomalies`
--

DROP TABLE IF EXISTS `performance_anomalies`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `performance_anomalies` (
  `anomaly_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `metric_name` varchar(100) NOT NULL,
  `expected_value` decimal(12,2) DEFAULT NULL,
  `actual_value` decimal(12,2) DEFAULT NULL,
  `deviation_percentage` decimal(5,2) DEFAULT NULL,
  `severity` enum('low','medium','high','critical') NOT NULL,
  `detected_date` date NOT NULL,
  `is_resolved` tinyint(1) DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`anomaly_id`),
  KEY `idx_client_severity` (`client_id`,`severity`),
  KEY `idx_detected_date` (`detected_date`),
  CONSTRAINT `performance_anomalies_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `performance_anomalies`
--

LOCK TABLES `performance_anomalies` WRITE;
/*!40000 ALTER TABLE `performance_anomalies` DISABLE KEYS */;
/*!40000 ALTER TABLE `performance_anomalies` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `permissions`
--

DROP TABLE IF EXISTS `permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `permissions` (
  `permission_id` int NOT NULL AUTO_INCREMENT,
  `permission_name` varchar(100) NOT NULL,
  `permission_key` varchar(100) NOT NULL,
  `description` text,
  `module` varchar(50) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`permission_id`),
  UNIQUE KEY `permission_name` (`permission_name`),
  UNIQUE KEY `permission_key` (`permission_key`),
  KEY `idx_permission_key` (`permission_key`),
  KEY `idx_module` (`module`)
) ENGINE=InnoDB AUTO_INCREMENT=51 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `permissions`
--

LOCK TABLES `permissions` WRITE;
/*!40000 ALTER TABLE `permissions` DISABLE KEYS */;
INSERT INTO `permissions` VALUES (1,'View Users','users.view','View all users in the system','user_management','2025-11-16 00:34:37'),(2,'Create Users','users.create','Create new users','user_management','2025-11-16 00:34:37'),(3,'Edit Users','users.edit','Edit user information','user_management','2025-11-16 00:34:37'),(4,'Delete Users','users.delete','Delete users from system','user_management','2025-11-16 00:34:37'),(5,'Suspend Users','users.suspend','Suspend/unsuspend user accounts','user_management','2025-11-16 00:34:37'),(6,'Change User Roles','users.change_role','Change user roles','user_management','2025-11-16 00:34:37'),(7,'View Permissions','permissions.view','View all permissions','access_control','2025-11-16 00:34:37'),(8,'Manage Permissions','permissions.manage','Assign/revoke permissions','access_control','2025-11-16 00:34:37'),(9,'View Audit Logs','audit.view','View access control audit logs','access_control','2025-11-16 00:34:37'),(10,'View All Clients','clients.view_all','View all client information','client_management','2025-11-16 00:34:37'),(11,'View Assigned Clients','clients.view_assigned','View only assigned clients','client_management','2025-11-16 00:34:37'),(12,'Edit Clients','clients.edit','Edit client profiles','client_management','2025-11-16 00:34:37'),(13,'Assign Employees','clients.assign_employees','Assign employees to clients','client_management','2025-11-16 00:34:37'),(14,'View All Tasks','tasks.view_all','View all tasks','task_management','2025-11-16 00:34:37'),(15,'View Assigned Tasks','tasks.view_assigned','View only assigned tasks','task_management','2025-11-16 00:34:37'),(16,'Create Tasks','tasks.create','Create new tasks','task_management','2025-11-16 00:34:37'),(17,'Edit Tasks','tasks.edit','Edit task information','task_management','2025-11-16 00:34:37'),(18,'Delete Tasks','tasks.delete','Delete tasks','task_management','2025-11-16 00:34:37'),(19,'Assign Tasks','tasks.assign','Assign tasks to employees','task_management','2025-11-16 00:34:37'),(20,'View Proposals','proposals.view','View project proposals','project_planner','2025-11-16 00:34:37'),(21,'Create Proposals','proposals.create','Create project proposals','project_planner','2025-11-16 00:34:37'),(22,'Edit Proposals','proposals.edit','Edit project proposals','project_planner','2025-11-16 00:34:37'),(23,'Send Proposals','proposals.send','Send proposals to clients','project_planner','2025-11-16 00:34:37'),(24,'View Campaigns','campaigns.view','View communication campaigns','communication','2025-11-16 00:34:37'),(25,'Create Campaigns','campaigns.create','Create communication campaigns','communication','2025-11-16 00:34:37'),(26,'Edit Campaigns','campaigns.edit','Edit communication campaigns','communication','2025-11-16 00:34:37'),(27,'Send Campaigns','campaigns.send','Send/schedule campaigns','communication','2025-11-16 00:34:37'),(28,'View Content','content.view','View content library','content','2025-11-16 00:34:37'),(29,'Create Content','content.create','Create new content','content','2025-11-16 00:34:37'),(30,'Edit Content','content.edit','Edit existing content','content','2025-11-16 00:34:37'),(31,'Publish Content','content.publish','Publish/approve content','content','2025-11-16 00:34:37'),(32,'View Posts','social.view','View social media posts','social_media','2025-11-16 00:34:37'),(33,'Create Posts','social.create','Create social media posts','social_media','2025-11-16 00:34:37'),(34,'Schedule Posts','social.schedule','Schedule social media posts','social_media','2025-11-16 00:34:37'),(35,'Publish Posts','social.publish','Publish social media posts','social_media','2025-11-16 00:34:37'),(36,'View SEO Projects','seo.view','View SEO projects','seo','2025-11-16 00:34:37'),(37,'Create SEO Projects','seo.create','Create SEO projects','seo','2025-11-16 00:34:37'),(38,'Run SEO Audits','seo.audit','Run SEO audits','seo','2025-11-16 00:34:37'),(39,'View Media','media.view','View media library','media_studio','2025-11-16 00:34:37'),(40,'Generate Media','media.generate','Generate AI media','media_studio','2025-11-16 00:34:37'),(41,'View Ad Campaigns','ads.view','View ad campaigns','ad_strategy','2025-11-16 00:34:37'),(42,'Create Ad Campaigns','ads.create','Create ad campaigns','ad_strategy','2025-11-16 00:34:37'),(43,'Edit Ad Campaigns','ads.edit','Edit ad campaigns','ad_strategy','2025-11-16 00:34:37'),(44,'Publish Ads','ads.publish','Publish ads to platforms','ad_strategy','2025-11-16 00:34:37'),(45,'View Analytics','analytics.view','View analytics dashboard','analytics','2025-11-16 00:34:37'),(46,'Export Reports','analytics.export','Export analytics reports','analytics','2025-11-16 00:34:37'),(47,'View Finance','finance.view','View financial data','finance','2025-11-16 00:34:37'),(48,'Manage Finance','finance.manage','Manage financial records','finance','2025-11-16 00:34:37'),(49,'View Packages','packages.view','View package information','packages','2025-11-16 00:34:37'),(50,'Manage Packages','packages.manage','Create/edit packages','packages','2025-11-16 00:34:37');
/*!40000 ALTER TABLE `permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `platform_best_times`
--

DROP TABLE IF EXISTS `platform_best_times`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `platform_best_times` (
  `best_time_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `platform` varchar(50) NOT NULL,
  `day_of_week` tinyint NOT NULL,
  `hour_of_day` tinyint NOT NULL,
  `engagement_score` decimal(5,2) DEFAULT NULL,
  `last_calculated` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`best_time_id`),
  UNIQUE KEY `unique_client_platform_time` (`client_id`,`platform`,`day_of_week`,`hour_of_day`),
  KEY `idx_client_platform` (`client_id`,`platform`),
  CONSTRAINT `platform_best_times_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `platform_best_times`
--

LOCK TABLES `platform_best_times` WRITE;
/*!40000 ALTER TABLE `platform_best_times` DISABLE KEYS */;
INSERT INTO `platform_best_times` VALUES (1,17,'facebook',2,11,87.20,'2025-11-15 10:30:59'),(2,17,'facebook',3,15,89.10,'2025-11-15 10:30:59'),(3,17,'facebook',4,10,90.40,'2025-11-15 10:30:59'),(4,17,'facebook',5,12,88.70,'2025-11-15 10:30:59'),(5,17,'facebook',6,9,86.50,'2025-11-15 10:30:59'),(6,17,'instagram',0,11,87.20,'2025-11-15 10:34:10'),(7,17,'instagram',2,13,85.60,'2025-11-15 10:34:10'),(8,17,'instagram',3,15,88.10,'2025-11-15 10:34:10'),(9,17,'instagram',4,9,86.40,'2025-11-15 10:34:10'),(10,17,'instagram',6,10,83.70,'2025-11-15 10:34:10');
/*!40000 ALTER TABLE `platform_best_times` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `project_proposals`
--

DROP TABLE IF EXISTS `project_proposals`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `project_proposals` (
  `proposal_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `created_by` int NOT NULL,
  `business_type` varchar(100) DEFAULT NULL,
  `budget` decimal(12,2) DEFAULT NULL,
  `challenges` text,
  `target_audience` text,
  `existing_presence` json DEFAULT NULL,
  `executive_summary` json DEFAULT NULL,
  `ai_generated_strategy` json DEFAULT NULL,
  `custom_strategy_html` text,
  `competitive_differentiators` json DEFAULT NULL,
  `custom_differentiators_html` text,
  `suggested_timeline` json DEFAULT NULL,
  `custom_timeline_html` text,
  `status` enum('draft','sent','accepted','rejected','scheduled') DEFAULT 'draft',
  `sent_at` timestamp NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `is_editable` tinyint(1) DEFAULT '1' COMMENT 'Can staff edit this proposal',
  `tone` varchar(50) DEFAULT 'professional' COMMENT 'Tone: professional, casual, technical',
  `sections_included` json DEFAULT NULL COMMENT 'Array of sections to include',
  `custom_notes` text COMMENT 'Custom notes added by staff',
  `scheduled_send_time` datetime DEFAULT NULL COMMENT 'When to send if scheduled',
  `company_name` varchar(255) DEFAULT NULL COMMENT 'Client company name',
  PRIMARY KEY (`proposal_id`),
  KEY `created_by` (`created_by`),
  KEY `idx_client_id` (`client_id`),
  KEY `idx_status` (`status`),
  KEY `idx_scheduled_send` (`scheduled_send_time`,`status`),
  CONSTRAINT `project_proposals_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `project_proposals_ibfk_2` FOREIGN KEY (`created_by`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `project_proposals`
--

LOCK TABLES `project_proposals` WRITE;
/*!40000 ALTER TABLE `project_proposals` DISABLE KEYS */;
INSERT INTO `project_proposals` VALUES (2,5,1,'ecommerce',180.00,'Low conversion rate','Ladies','{\"platforms\": [\"website\", \"instagram\", \"facebook\", \"linkedin\"]}',NULL,'{\"note\": \"Generated using fallback template\", \"campaigns\": {\"seo\": {\"focus\": \"On-page + Content\"}, \"social_media\": {\"platforms\": [\"Instagram\", \"Facebook\", \"LinkedIn\"]}, \"email_marketing\": {\"frequency\": \"2-3 per week\"}, \"paid_advertising\": {\"platforms\": [\"Meta Ads\", \"Google Ads\"], \"budget_allocation\": \"60%\"}}}',NULL,'{\"differentiators\": [{\"title\": \"AI-Powered Automation\", \"description\": \"Faster deployment with advanced automation\"}, {\"title\": \"Data-Driven Optimization\", \"description\": \"Continuous optimization for maximum ROI\"}]}',NULL,'{\"phases\": [{\"phase\": \"Setup & Discovery\", \"duration\": \"Week 1-2\", \"deliverables\": [\"Strategy document\", \"Analytics setup\"]}, {\"phase\": \"Launch\", \"duration\": \"Week 3-6\", \"deliverables\": [\"Live campaigns\", \"Content calendar\"]}, {\"phase\": \"Growth\", \"duration\": \"Month 3-6\", \"deliverables\": [\"Scaled campaigns\", \"ROI reports\"]}]}',NULL,'draft',NULL,'2025-11-13 07:02:52','2025-11-13 07:02:52',1,'professional',NULL,NULL,NULL,NULL),(3,6,1,'ecommerce',180.00,'low click rates','ladies','{\"platforms\": [\"website\", \"instagram\", \"facebook\", \"linkedin\"]}',NULL,'{\"kpis\": {\"month_1\": {\"leads\": \"50-100\", \"conversions\": \"10-20\", \"website_traffic\": \"500-1000 visitors\"}, \"month_3\": {\"leads\": \"200-300\", \"conversions\": \"50-75\", \"website_traffic\": \"2000-3000 visitors\"}, \"month_6\": {\"leads\": \"500+\", \"conversions\": \"150+\", \"website_traffic\": \"5000+ visitors\"}}, \"campaigns\": {\"seo\": {\"focus\": \"On-page optimization and content strategy\", \"timeline\": \"3-6 months for results\", \"content_plan\": \"Weekly blog posts + technical SEO\", \"keyword_targets\": \"50-100 keywords\"}, \"social_media\": {\"platforms\": [\"Instagram\", \"Facebook\", \"LinkedIn\"], \"content_types\": [\"Stories\", \"Reels\", \"Posts\", \"Live\"], \"posting_frequency\": \"Daily\", \"engagement_strategy\": \"Community management + influencer partnerships\"}, \"email_marketing\": {\"tools\": [\"Mailchimp\", \"SendGrid\"], \"strategy\": \"Segmented campaigns with automation\", \"frequency\": \"2-3 emails per week\", \"expected_open_rate\": \"25-35%\"}, \"paid_advertising\": {\"formats\": [\"Search Ads\", \"Display Ads\", \"Video Ads\", \"Carousel Ads\"], \"platforms\": [\"Meta (Facebook & Instagram)\", \"Google Ads\"], \"expected_roi\": \"300-400%\", \"budget_allocation\": \"60% of total budget\"}}, \"automation_tools\": [\"HubSpot for CRM and email automation\", \"Hootsuite for social media scheduling\", \"Google Analytics 4 for tracking\", \"Meta Business Suite for ad management\", \"Zapier for workflow automation\"]}',NULL,'{\"differentiators\": [{\"title\": \"AI-Powered Automation\", \"impact\": \"Faster deployment, reduced costs\", \"description\": \"Deploy campaigns 70% faster using our proprietary AI automation tools, reducing manual work and accelerating time-to-market.\"}, {\"title\": \"Hyper-Personalized Targeting\", \"impact\": \"Higher conversion rates, better ROAS\", \"description\": \"Our AI analyzes thousands of data points to create highly targeted audience segments, improving ad relevance and conversion rates by 2-3x.\"}, {\"title\": \"Integrated Online-Offline Strategy\", \"impact\": \"Omnichannel presence, increased revenue\", \"description\": \"We bridge digital and physical touchpoints, creating seamless customer journeys that drive both online conversions and foot traffic.\"}, {\"title\": \"Cost-Efficient Media Optimization\", \"impact\": \"20-30% cost reduction, improved ROI\", \"description\": \"Our AI continuously optimizes ad spend across platforms, ensuring you get maximum results for minimum investment.\"}, {\"title\": \"Predictive Performance Analytics\", \"impact\": \"Data-driven decisions, reduced risk\", \"description\": \"Advanced machine learning models forecast campaign performance, allowing proactive adjustments before budget is wasted.\"}]}',NULL,'{\"phases\": [{\"phase\": \"Discovery & Setup\", \"duration\": \"Week 1-2\", \"milestones\": [\"Complete brand audit\", \"Finalize target audience personas\", \"Set up tracking and analytics\", \"Establish KPI baselines\"], \"deliverables\": [\"Marketing strategy document\", \"Audience personas\", \"Analytics dashboard setup\"]}, {\"phase\": \"Campaign Development\", \"duration\": \"Week 3-4\", \"milestones\": [\"Create ad campaigns\", \"Develop content calendar\", \"Design creative assets\", \"Set up automation workflows\"], \"deliverables\": [\"Ad creatives (20-30 variations)\", \"Content calendar (3 months)\", \"Email templates\", \"Landing pages\"]}, {\"phase\": \"Launch & Optimization\", \"duration\": \"Week 5-8\", \"milestones\": [\"Launch paid campaigns\", \"Begin organic content posting\", \"Start email sequences\", \"A/B test key elements\"], \"deliverables\": [\"Live campaigns across all platforms\", \"Weekly performance reports\", \"Optimization recommendations\"]}, {\"phase\": \"Scale & Growth\", \"duration\": \"Month 3-6\", \"milestones\": [\"Scale winning campaigns\", \"Expand to new platforms\", \"Implement advanced automation\", \"Launch retargeting campaigns\"], \"deliverables\": [\"Monthly strategy reviews\", \"ROI reports\", \"Growth projections\", \"Quarterly business reviews\"]}], \"expected_results\": {\"month_1\": \"Foundation established, initial traction\", \"month_3\": \"Consistent lead flow, positive ROI\", \"month_6\": \"Scalable growth, 3-4x ROI achieved\"}}',NULL,'sent','2025-11-13 08:12:01','2025-11-13 07:09:22','2025-11-13 08:12:01',1,'professional','[\"strategy\", \"differentiators\", \"timeline\"]','','2025-11-15 07:30:00',NULL),(4,7,1,'software',100.00,'lock click rates','SME business','{\"platforms\": [\"website\", \"facebook\", \"instagram\", \"google_ads\"]}',NULL,'{\"kpis\": {\"month_1\": {\"leads\": \"50-100\", \"conversions\": \"10-20\", \"website_traffic\": \"500-1000 visitors\"}, \"month_3\": {\"leads\": \"200-300\", \"conversions\": \"50-75\", \"website_traffic\": \"2000-3000 visitors\"}, \"month_6\": {\"leads\": \"500+\", \"conversions\": \"150+\", \"website_traffic\": \"5000+ visitors\"}}, \"campaigns\": {\"seo\": {\"focus\": \"On-page optimization and content strategy\", \"timeline\": \"3-6 months for results\", \"content_plan\": \"Weekly blog posts + technical SEO\", \"keyword_targets\": \"50-100 keywords\"}, \"social_media\": {\"platforms\": [\"Instagram\", \"Facebook\", \"LinkedIn\"], \"content_types\": [\"Stories\", \"Reels\", \"Posts\", \"Live\"], \"posting_frequency\": \"Daily\", \"engagement_strategy\": \"Community management + influencer partnerships\"}, \"email_marketing\": {\"tools\": [\"Mailchimp\", \"SendGrid\"], \"strategy\": \"Segmented campaigns with automation\", \"frequency\": \"2-3 emails per week\", \"expected_open_rate\": \"25-35%\"}, \"paid_advertising\": {\"formats\": [\"Search Ads\", \"Display Ads\", \"Video Ads\", \"Carousel Ads\"], \"platforms\": [\"Meta (Facebook & Instagram)\", \"Google Ads\"], \"expected_roi\": \"300-400%\", \"budget_allocation\": \"60% of total budget\"}}, \"automation_tools\": [\"HubSpot for CRM and email automation\", \"Hootsuite for social media scheduling\", \"Google Analytics 4 for tracking\", \"Meta Business Suite for ad management\", \"Zapier for workflow automation\"]}','<h4>CAMPAIGNS:</h4><ul></ul><h4>• SEO: No</h4><ul></ul><h4>• SOCIAL MEDIA: Instagram, Facebook, LinkedIn</h4><ul></ul><h4>• EMAIL MARKETING: </h4><ul></ul><h4>• PAID ADVERTISING: Meta (Facebook &amp; Instagram), Google Ads</h4><ul></ul><h4>AUTOMATION TOOLS:</h4><ul><li>HubSpot for CRM and email automation</li><li>Hootsuite for social media scheduling</li><li>Google Analytics 4 for tracking</li><li>Meta Business Suite for ad management</li><li>Zapier for workflow automation</li></ul>','{\"differentiators\": [{\"title\": \"AI-Powered Automation\", \"impact\": \"Faster deployment, reduced costs\", \"description\": \"Deploy campaigns 70% faster using our proprietary AI automation tools, reducing manual work and accelerating time-to-market.\"}, {\"title\": \"Hyper-Personalized Targeting\", \"impact\": \"Higher conversion rates, better ROAS\", \"description\": \"Our AI analyzes thousands of data points to create highly targeted audience segments, improving ad relevance and conversion rates by 2-3x.\"}, {\"title\": \"Integrated Online-Offline Strategy\", \"impact\": \"Omnichannel presence, increased revenue\", \"description\": \"We bridge digital and physical touchpoints, creating seamless customer journeys that drive both online conversions and foot traffic.\"}, {\"title\": \"Cost-Efficient Media Optimization\", \"impact\": \"20-30% cost reduction, improved ROI\", \"description\": \"Our AI continuously optimizes ad spend across platforms, ensuring you get maximum results for minimum investment.\"}, {\"title\": \"Predictive Performance Analytics\", \"impact\": \"Data-driven decisions, reduced risk\", \"description\": \"Advanced machine learning models forecast campaign performance, allowing proactive adjustments before budget is wasted.\"}]}','<div class=\"differentiator-card\"><h4>1. AI-Powered Automation</h4><p>Deploy campaigns 70% faster using our proprietary AI automation tools, reducing manual work and accelerating time-to-market.</p><p style=\"color: #10b981; font-weight: 600;\"><i class=\"ti ti-trending-up\"></i> Impact: Faster deployment, reduced costs</p></div><div class=\"differentiator-card\"><h4>2. Hyper-Personalized Targeting</h4><p>Our AI analyzes thousands of data points to create highly targeted audience segments, improving ad relevance and conversion rates by 2-3x.</p><p style=\"color: #10b981; font-weight: 600;\"><i class=\"ti ti-trending-up\"></i> Impact: Higher conversion rates, better ROAS</p></div><div class=\"differentiator-card\"><h4>3. Integrated Online-Offline Strategy</h4><p>We bridge digital and physical touchpoints, creating seamless customer journeys that drive both online conversions and foot traffic.</p><p style=\"color: #10b981; font-weight: 600;\"><i class=\"ti ti-trending-up\"></i> Impact: Omnichannel presence, increased revenue</p></div><div class=\"differentiator-card\"><h4>4. Cost-Efficient Media Optimization</h4><p>Our AI continuously optimizes ad spend across platforms, ensuring you get maximum results for minimum investment.</p><p style=\"color: #10b981; font-weight: 600;\"><i class=\"ti ti-trending-up\"></i> Impact: 20-30% cost reduction, improved ROI</p></div><div class=\"differentiator-card\"><h4>5. Predictive Performance Analytics</h4><p>Advanced machine learning models forecast campaign performance, allowing proactive adjustments before budget is wasted.</p><p style=\"color: #10b981; font-weight: 600;\"><i class=\"ti ti-trending-up\"></i> Impact: Data-driven decisions, reduced risk</p></div>','{\"phases\": [{\"phase\": \"Discovery & Setup\", \"duration\": \"Week 1-2\", \"milestones\": [\"Complete brand audit\", \"Finalize target audience personas\", \"Set up tracking and analytics\", \"Establish KPI baselines\"], \"deliverables\": [\"Marketing strategy document\", \"Audience personas\", \"Analytics dashboard setup\"]}, {\"phase\": \"Campaign Development\", \"duration\": \"Week 3-4\", \"milestones\": [\"Create ad campaigns\", \"Develop content calendar\", \"Design creative assets\", \"Set up automation workflows\"], \"deliverables\": [\"Ad creatives (20-30 variations)\", \"Content calendar (3 months)\", \"Email templates\", \"Landing pages\"]}, {\"phase\": \"Launch & Optimization\", \"duration\": \"Week 5-8\", \"milestones\": [\"Launch paid campaigns\", \"Begin organic content posting\", \"Start email sequences\", \"A/B test key elements\"], \"deliverables\": [\"Live campaigns across all platforms\", \"Weekly performance reports\", \"Optimization recommendations\"]}, {\"phase\": \"Scale & Growth\", \"duration\": \"Month 3-6\", \"milestones\": [\"Scale winning campaigns\", \"Expand to new platforms\", \"Implement advanced automation\", \"Launch retargeting campaigns\"], \"deliverables\": [\"Monthly strategy reviews\", \"ROI reports\", \"Growth projections\", \"Quarterly business reviews\"]}], \"expected_results\": {\"month_1\": \"Foundation established, initial traction\", \"month_3\": \"Consistent lead flow, positive ROI\", \"month_6\": \"Scalable growth, 3-4x ROI achieved\"}}','<div class=\"timeline-phase\"><h4>Discovery &amp; Setup (Week 1-2)</h4><ul><div class=\"timeline-phase\"><h4>Campaign Development (Week 3-4)</h4><ul><div class=\"timeline-phase\"><h4>Launch &amp; Optimization (Week 5-8)</h4><ul><div class=\"timeline-phase\"><h4>Scale &amp; Growth (Month 3-6)</h4><ul></ul></div></ul></div>\n            </ul></div>\n        \n                        </ul></div>\n                    ','scheduled',NULL,'2025-11-13 07:32:41','2025-11-13 08:31:56',1,'casual','[\"strategy\", \"differentiators\", \"timeline\"]',NULL,'2025-11-15 08:20:00',NULL),(6,7,1,'ecommerce',500.00,'low click rate','ladies','{\"platforms\": [\"website\", \"facebook\", \"instagram\", \"linkedin\", \"youtube\"]}',NULL,'{\"Budget\": \"$500.0\", \"Company\": \"hashnate\", \"ROI_Focus\": \"To increase the click rate, the focus will be on creating engaging content that resonates with the target audience. The success of the strategy will be measured by the increase in click rates, conversion rates, and ultimately, sales.\", \"Challenges\": \"low click rate\", \"BusinessType\": \"ecommerce\", \"TargetAudience\": \"ladies\", \"ExistingPresence\": {\"platforms\": [\"website\", \"facebook\", \"instagram\", \"linkedin\", \"youtube\"]}, \"MarketingStrategy\": {\"Campaigns\": [{\"type\": \"ad\", \"platform\": \"facebook\", \"content_topic\": \"product showcase\", \"creative_format\": \"video\", \"budget_allocation\": \"$150\"}, {\"type\": \"email\", \"platform\": \"mailchimp\", \"content_topic\": \"new arrivals\", \"creative_format\": \"newsletter\", \"budget_allocation\": \"$50\"}, {\"type\": \"SEO\", \"platform\": \"website\", \"content_topic\": \"how-to guides\", \"creative_format\": \"blog posts\", \"budget_allocation\": \"$100\"}, {\"type\": \"social media\", \"platform\": \"instagram\", \"content_topic\": \"product usage\", \"creative_format\": \"stories\", \"budget_allocation\": \"$200\"}], \"AutomationTools\": [{\"tool\": \"Hootsuite\", \"purpose\": \"schedule and post social media content\", \"monthly_cost\": \"$29\"}, {\"tool\": \"HubSpot\", \"purpose\": \"email marketing automation\", \"monthly_cost\": \"$50\"}, {\"tool\": \"SEMRush\", \"purpose\": \"SEO analysis and optimization\", \"monthly_cost\": \"$99\"}]}}','this is Marketing Strategy','{\"differentiators\": [{\"title\": \"Faster Deployment with Automation\", \"impact\": \"This allows your ecommerce business to respond faster to market changes, seize timely opportunities, and gain a competitive edge.\", \"description\": \"Our digital marketing agency leverages advanced automation tools to streamline campaign deployment, significantly reducing the time from conceptualization to execution.\"}, {\"title\": \"AI-Personalized Targeting\", \"impact\": \"Through AI-personalized targeting, your ecommerce business can improve customer engagement, increase conversion rates, and maximize marketing ROI.\", \"description\": \"We utilize Artificial Intelligence (AI) to analyze customer data and create personalized marketing messages. This ensures that your customers receive content that is most relevant to their preferences and behaviors.\"}, {\"title\": \"Cost-Efficiency\", \"impact\": \"This cost-efficiency approach ensures that your ecommerce business maximizes its marketing budget, driving more sales and profits.\", \"description\": \"Our digital marketing strategies are designed to optimize your advertising spend. We focus on high-impact channels and tactics to ensure that every dollar you spend yields the best possible return.\"}, {\"title\": \"Advanced Performance Tracking\", \"impact\": \"This allows your ecommerce business to make data-driven decisions, optimize marketing strategies, and achieve better results.\", \"description\": \"We provide comprehensive performance tracking, using advanced analytics tools to monitor and measure the effectiveness of your marketing campaigns.\"}]}','1. Faster Deployment with Automation\nOur digital marketing agency leverages advanced automation tools to streamline campaign deployment, significantly reducing the time from conceptualization to execution.\nImpact: This allows your ecommerce business to respond faster to market changes, seize timely opportunities, and gain a competitive edge.\n\n2. AI-Personalized Targeting\nWe utilize Artificial Intelligence (AI) to analyze customer data and create personalized marketing messages. This ensures that your customers receive content that is most relevant to their preferences and behaviors.\nImpact: Through AI-personalized targeting, your ecommerce business can improve customer engagement, increase conversion rates, and maximize marketing ROI.\n\n3. Cost-Efficiency\nOur digital marketing strategies are designed to optimize your advertising spend. We focus on high-impact channels and tactics to ensure that every dollar you spend yields the best possible return.\nImpact: This cost-efficiency approach ensures that your ecommerce business maximizes its marketing budget, driving more sales and profits.\n\n4. Advanced Performance Tracking\nWe provide comprehensive performance tracking, using advanced analytics tools to monitor and measure the effectiveness of your marketing campaigns.\nImpact: This allows your ecommerce business to make data-driven decisions, optimize marketing strategies, and achieve better results.\n\n','{\"project\": {\"budget\": \"$500.0\", \"phases\": [{\"phase\": \"Phase 1: Market Research\", \"duration\": \"2 weeks\", \"milestones\": [\"Identify target market\", \"Competitor analysis\", \"Establish marketing goals\"], \"deliverables\": [\"Market research report\", \"Competitor analysis report\", \"Marketing goals\"]}, {\"phase\": \"Phase 2: Strategy Development\", \"duration\": \"3 weeks\", \"milestones\": [\"Develop marketing strategy\", \"Identify marketing channels\", \"Establish marketing budget\"], \"deliverables\": [\"Marketing strategy document\", \"Marketing channels list\", \"Marketing budget breakdown\"]}, {\"phase\": \"Phase 3: Content Creation\", \"duration\": \"4 weeks\", \"milestones\": [\"Create marketing content\", \"Review and revise content\", \"Finalize marketing content\"], \"deliverables\": [\"Marketing content drafts\", \"Revised marketing content\", \"Final marketing content\"]}, {\"phase\": \"Phase 4: Campaign Launch\", \"duration\": \"1 week\", \"milestones\": [\"Launch marketing campaign\", \"Monitor campaign performance\", \"Make necessary adjustments\"], \"deliverables\": [\"Launched marketing campaign\", \"Campaign performance report\", \"Adjusted campaign strategy\"]}, {\"phase\": \"Phase 5: Campaign Evaluation\", \"duration\": \"2 weeks\", \"milestones\": [\"Evaluate campaign performance\", \"Identify areas of improvement\", \"Plan for future campaigns\"], \"deliverables\": [\"Campaign evaluation report\", \"Improvement plan\", \"Future campaign strategy\"]}]}}','','scheduled',NULL,'2025-11-13 08:46:35','2025-11-13 08:54:36',1,'professional',NULL,NULL,'2025-11-16 08:49:00',NULL),(7,9,1,'Engine Oil',300.00,'Low click rate','Everyone','{\"platforms\": [\"website\", \"linkedin\", \"google_ads\"]}',NULL,'{\"budget\": 300.0, \"company\": \"hashnate\", \"strategy\": {\"campaigns\": [{\"type\": \"ad\", \"platform\": \"google_ads\", \"content_topic\": \"Benefits of using hashnate engine oil\", \"creative_format\": \"Video Ads\", \"budget_percentage\": 40}, {\"type\": \"email\", \"platform\": \"Mailchimp\", \"content_topic\": \"Maintenance tips for your vehicle with hashnate engine oil\", \"creative_format\": \"Newsletter\", \"budget_percentage\": 20}, {\"type\": \"SEO\", \"platform\": \"website\", \"content_topic\": \"Comparison of hashnate engine oil with other brands\", \"creative_format\": \"Blog Posts\", \"budget_percentage\": 20}, {\"type\": \"social_media\", \"platform\": \"linkedin\", \"content_topic\": \"The science behind hashnate engine oil\", \"creative_format\": \"Infographic\", \"budget_percentage\": 20}], \"automation_tools\": [{\"use\": \"Track website traffic and user behavior\", \"tool\": \"Google Analytics\"}, {\"use\": \"Automate email marketing campaigns\", \"tool\": \"Mailchimp\"}, {\"use\": \"Schedule and manage social media posts\", \"tool\": \"Hootsuite\"}, {\"use\": \"Monitor SEO performance\", \"tool\": \"Moz\"}]}, \"challenges\": \"Low click rate\", \"business_type\": \"Engine Oil\", \"target_audience\": \"Everyone\", \"existing_presence\": {\"platforms\": [\"website\", \"linkedin\", \"google_ads\"]}}','<p>\n        </p><h3>Digital Marketing Proposal</h3><p>\n        </p><p style=\"text-align: center; color: #1DD8FC; font-size: 20px; margin-bottom: 3rem;\">Prepared for </p><p>\n        \n        </p><h2>Executive Summary</h2><p>\n        </p><p>This comprehensive digital marketing proposal has been specifically designed for , a  looking to enhance their digital presence and drive measurable growth.</p><p>\n        </p><p>Our AI-powered approach combines cutting-edge marketing technology with proven strategies to deliver exceptional results within your investment budget of <strong>$0</strong>.</p><p>\n        \n        </p><h2>Client Information</h2><p>\n        </p><p><br></p><p>\n        \n        </p><h2>Current Challenges</h2><p>\n        </p><p><br></p><p>\n        \n        </p><h2>Target Audience</h2><p>\n        </p><p><br></p><p>\n    \n        </p><h2>Next Steps</h2><p>\n        </p><p>We\'re excited about the opportunity to partner with  and help you achieve your digital marketing goals. Our team is ready to begin implementation as soon as you\'re ready.</p><p>\n        </p><p><strong>Let\'s transform your digital presence together!</strong></p><p>\n    </p>','{\"differentiators\": [{\"title\": \"Faster Deployment with Automation\", \"impact\": \"This allows you to reach your target audience faster and more efficiently, reducing the time-to-market and enabling quick adjustments to your marketing strategy.\", \"description\": \"Our digital marketing agency leverages the latest automation tools to ensure a swift and seamless execution of your online marketing campaigns.\"}, {\"title\": \"AI-Personalized Targeting\", \"impact\": \"With AI-personalized targeting, your marketing campaigns will achieve higher engagement rates and better conversion rates, maximizing your return on investment.\", \"description\": \"We use advanced AI technology to analyze your target audience\'s behavior and preferences. This allows us to create highly personalized marketing messages that resonate with your audience.\"}, {\"title\": \"Cost-Efficiency\", \"impact\": \"This approach ensures that you get the most value for your marketing budget, helping you achieve your business goals without breaking the bank.\", \"description\": \"Our digital marketing strategies are designed to maximize your budget. We focus on high-impact, cost-effective tactics that deliver the best results for your investment.\"}, {\"title\": \"Advanced Performance Tracking\", \"impact\": \"With our advanced performance tracking, you will always know how your campaigns are performing and where to focus your efforts for the greatest impact.\", \"description\": \"We provide real-time tracking of your marketing campaigns, using advanced analytics to measure performance and identify opportunities for improvement.\"}]}','1. Faster Deployment with Automation\nOur digital marketing agency leverages the latest automation tools to ensure a swift and seamless execution of your online marketing campaigns.\nImpact: This allows you to reach your target audience faster and more efficiently, reducing the time-to-market and enabling quick adjustments to your marketing strategy.\n\n2. AI-Personalized Targeting\nWe use advanced AI technology to analyze your target audience\'s behavior and preferences. This allows us to create highly personalized marketing messages that resonate with your audience.\nImpact: With AI-personalized targeting, your marketing campaigns will achieve higher engagement rates and better conversion rates, maximizing your return on investment.\n\n3. Cost-Efficiency\nOur digital marketing strategies are designed to maximize your budget. We focus on high-impact, cost-effective tactics that deliver the best results for your investment.\nImpact: This approach ensures that you get the most value for your marketing budget, helping you achieve your business goals without breaking the bank.\n\n4. Advanced Performance Tracking\nWe provide real-time tracking of your marketing campaigns, using advanced analytics to measure performance and identify opportunities for improvement.\nImpact: With our advanced performance tracking, you will always know how your campaigns are performing and where to focus your efforts for the greatest impact.\n\n','{\"project\": {\"budget\": 300.0, \"phases\": [{\"phase\": \"Research\", \"duration\": \"2 weeks\", \"milestones\": [\"Define target audience\", \"Competitor analysis\", \"Market trends identification\"], \"deliverables\": [\"Research report\", \"Target audience profile\", \"Competitor analysis report\", \"Market trends report\"]}, {\"phase\": \"Strategy Development\", \"duration\": \"2 weeks\", \"milestones\": [\"Marketing objectives definition\", \"Marketing strategies formulation\", \"Marketing mix decisions\"], \"deliverables\": [\"Marketing plan\", \"Marketing strategy document\"]}, {\"phase\": \"Creative Development\", \"duration\": \"3 weeks\", \"milestones\": [\"Creation of marketing materials\", \"Marketing message development\", \"Visual identity design\"], \"deliverables\": [\"Marketing materials\", \"Marketing message\", \"Visual identity\"]}, {\"phase\": \"Implementation\", \"duration\": \"4 weeks\", \"milestones\": [\"Marketing campaigns launch\", \"Monitoring of marketing activities\", \"Adjustments of marketing strategies\"], \"deliverables\": [\"Marketing campaigns\", \"Monitoring report\", \"Adjusted marketing strategies\"]}, {\"phase\": \"Evaluation\", \"duration\": \"2 weeks\", \"milestones\": [\"Marketing results analysis\", \"Marketing effectiveness evaluation\", \"Recommendations for future marketing activities\"], \"deliverables\": [\"Marketing results report\", \"Marketing effectiveness evaluation report\", \"Recommendations report\"]}]}}','=== Research ===\nDuration: 2 weeks\nMilestones:\n- Define target audience\n- Competitor analysis\n- Market trends identification\nDeliverables:\n- Research report\n- Target audience profile\n- Competitor analysis report\n- Market trends report\n\n=== Strategy Development ===\nDuration: 2 weeks\nMilestones:\n- Marketing objectives definition\n- Marketing strategies formulation\n- Marketing mix decisions\nDeliverables:\n- Marketing plan\n- Marketing strategy document\n\n=== Creative Development ===\nDuration: 3 weeks\nMilestones:\n- Creation of marketing materials\n- Marketing message development\n- Visual identity design\nDeliverables:\n- Marketing materials\n- Marketing message\n- Visual identity\n\n=== Implementation ===\nDuration: 4 weeks\nMilestones:\n- Marketing campaigns launch\n- Monitoring of marketing activities\n- Adjustments of marketing strategies\nDeliverables:\n- Marketing campaigns\n- Monitoring report\n- Adjusted marketing strategies\n\n=== Evaluation ===\nDuration: 2 weeks\nMilestones:\n- Marketing results analysis\n- Marketing effectiveness evaluation\n- Recommendations for future marketing activities\nDeliverables:\n- Marketing results report\n- Marketing effectiveness evaluation report\n- Recommendations report\n\n','sent','2025-11-13 09:04:53','2025-11-13 08:57:05','2025-11-13 12:29:30',1,'professional',NULL,'Auto-saved content',NULL,NULL),(8,10,1,'Real Estate',10000.00,'low website traffic','Business owners','{\"website\": true, \"facebook\": true, \"linkedin\": true, \"instagram\": true}',NULL,'{\"budget\": 10000.0, \"company\": \"hashnate\", \"strategy\": {\"campaigns\": [{\"type\": \"ad\", \"platform\": \"Google Adwords\", \"contentTopic\": \"Benefits of investing in real estate\", \"creativeFormat\": \"video\", \"budgetAllocation\": 3000.0}, {\"type\": \"email\", \"platform\": \"Mailchimp\", \"contentTopic\": \"Latest real estate trends for business owners\", \"creativeFormat\": \"newsletter\", \"budgetAllocation\": 1000.0}, {\"type\": \"SEO\", \"platform\": \"Website\", \"contentTopic\": \"How real estate can boost your business\", \"creativeFormat\": \"blog post\", \"budgetAllocation\": 2000.0}, {\"type\": \"social media\", \"platform\": \"LinkedIn\", \"contentTopic\": \"Success stories of business owners in real estate\", \"creativeFormat\": \"carousel\", \"budgetAllocation\": 4000.0}], \"automationTools\": [{\"tool\": \"HubSpot\", \"useCase\": \"CRM and email marketing automation\", \"budgetAllocation\": 500.0}, {\"tool\": \"Hootsuite\", \"useCase\": \"Social media management and scheduling\", \"budgetAllocation\": 500.0}, {\"tool\": \"SEMRush\", \"useCase\": \"SEO management and analysis\", \"budgetAllocation\": 500.0}, {\"tool\": \"Google Analytics\", \"useCase\": \"Website traffic analysis\", \"budgetAllocation\": 0.0}]}, \"challenges\": \"low website traffic\", \"businessType\": \"Real Estate\", \"targetAudience\": \"Business owners\", \"existingPresence\": {\"website\": true, \"facebook\": true, \"linkedin\": true, \"instagram\": true}}',NULL,'{\"differentiators\": [{\"title\": \"Faster Deployment with Automation\", \"impact\": \"This leads to quicker results and allows your real estate services to reach potential customers faster than your competitors.\", \"description\": \"Our agency utilizes cutting-edge automation tools to expedite campaign setup and execution. This allows us to launch campaigns faster and with greater precision.\"}, {\"title\": \"AI-Personalized Targeting\", \"impact\": \"This results in more effective ad spend and higher conversion rates, as your ads are tailored to highly relevant audiences.\", \"description\": \"We leverage artificial intelligence to create personalized ad targeting. This ensures your ads are shown to individuals who are most likely to be interested in your real estate services.\"}, {\"title\": \"Cost-Efficiency\", \"impact\": \"This ensures you get the most out of your marketing budget, allowing you to invest more in other growth areas.\", \"description\": \"Our digital marketing strategies are designed to maximize ROI. We focus on cost-effective strategies and prioritize channels that deliver the best returns for your budget.\"}, {\"title\": \"Advanced Performance Tracking\", \"impact\": \"This data-driven approach ensures transparency and allows you to easily measure the return on your marketing investment.\", \"description\": \"We provide comprehensive performance tracking and reporting, with real-time access to key metrics. This allows you to easily monitor the success of your campaigns and make informed decisions.\"}]}',NULL,'{\"project\": {\"budget\": 10000, \"timeline\": {\"phases\": [{\"phase\": \"Phase 1: Market Research\", \"duration\": \"1 month\", \"milestones\": [\"Identify target audience\", \"Analyze competitors\", \"Identify market trends\"], \"deliverables\": [\"Comprehensive market research report\", \"Target audience profile\", \"Competitor analysis report\"]}, {\"phase\": \"Phase 2: Strategy Development\", \"duration\": \"1 month\", \"milestones\": [\"Formulate marketing objectives\", \"Develop marketing strategies\", \"Identify marketing channels\"], \"deliverables\": [\"Marketing objectives document\", \"Marketing strategy plan\", \"Marketing channels report\"]}, {\"phase\": \"Phase 3: Campaign Development\", \"duration\": \"2 months\", \"milestones\": [\"Develop campaign concepts\", \"Create campaign materials\", \"Test campaign effectiveness\"], \"deliverables\": [\"Campaign concepts document\", \"Campaign materials\", \"Campaign effectiveness report\"]}, {\"phase\": \"Phase 4: Campaign Execution\", \"duration\": \"3 months\", \"milestones\": [\"Launch marketing campaign\", \"Monitor campaign performance\", \"Optimize campaign based on performance\"], \"deliverables\": [\"Campaign launch report\", \"Campaign performance report\", \"Campaign optimization report\"]}, {\"phase\": \"Phase 5: Post-Campaign Analysis\", \"duration\": \"1 month\", \"milestones\": [\"Analyze campaign results\", \"Identify areas of improvement\", \"Formulate future strategies\"], \"deliverables\": [\"Post-campaign analysis report\", \"Improvement plan\", \"Future strategies document\"]}]}}}',NULL,'draft',NULL,'2025-11-13 12:03:18','2025-11-13 12:03:18',1,'professional',NULL,NULL,NULL,NULL),(9,11,1,'Restaurant',10000.00,'low website traffic','Girls','{\"website\": true, \"youtube\": true, \"facebook\": true, \"linkedin\": true, \"instagram\": true}',NULL,'{\"budget\": 10000.0, \"company\": \"hashnate\", \"strategy\": {\"campaigns\": [{\"type\": \"ad\", \"platform\": \"Google Ads\", \"content_topics\": [\"new menu items\", \"special events\", \"chef\'s specials\"], \"creative_format\": \"video\", \"budget_percentage\": 30}, {\"type\": \"email\", \"platform\": \"Mailchimp\", \"content_topics\": [\"exclusive offers\", \"menu updates\", \"event invitations\"], \"creative_format\": \"infographics\", \"budget_percentage\": 20}, {\"type\": \"SEO\", \"platform\": \"Google Search Console\", \"content_topics\": [\"restaurant reviews\", \"food recipes\", \"behind the scenes\"], \"creative_format\": \"blog posts\", \"budget_percentage\": 15}, {\"type\": \"social media\", \"platform\": \"Instagram\", \"content_topics\": [\"daily specials\", \"customer testimonials\", \"behind the scenes\"], \"creative_format\": \"photos and short videos\", \"budget_percentage\": 35}], \"automation_tools\": [{\"tool\": \"Hootsuite\", \"purpose\": \"to schedule and manage social media posts\"}, {\"tool\": \"Google Analytics\", \"purpose\": \"to track website traffic and user behavior\"}, {\"tool\": \"Mailchimp\", \"purpose\": \"to automate email marketing campaigns\"}, {\"tool\": \"SEMRush\", \"purpose\": \"to track keyword rankings and optimize SEO\"}, {\"tool\": \"AdEspresso\", \"purpose\": \"to optimize and manage Google Ads\"}]}, \"challenges\": \"low website traffic\", \"business_type\": \"restaurant\", \"target_audience\": \"girls\", \"existing_presence\": {\"website\": true, \"youtube\": true, \"facebook\": true, \"linkedin\": true, \"instagram\": true}}',NULL,'{\"differentiators\": [{\"title\": \"Faster Deployment with Automation\", \"impact\": \"This allows for faster deployment of marketing campaigns, providing your restaurant business with a competitive edge.\", \"description\": \"Our agency uses advanced automation tools to streamline your marketing process, reducing time spent on repetitive tasks.\"}, {\"title\": \"AI-Personalized Targeting\", \"impact\": \"This means more relevant ads to potential customers, increasing engagement and conversion rates.\", \"description\": \"We utilize artificial intelligence to analyze customer behavior and preferences, enabling highly personalized targeting.\"}, {\"title\": \"Cost-Efficiency\", \"impact\": \"This helps your restaurant save on marketing costs while still achieving significant results.\", \"description\": \"Our digital marketing strategies are designed to maximize your budget, focusing on high-ROI activities.\"}, {\"title\": \"Advanced Performance Tracking\", \"impact\": \"This allows for real-time optimization of your marketing campaigns, ensuring that they deliver the desired results.\", \"description\": \"Our agency provides comprehensive performance tracking using cutting-edge tools and metrics.\"}]}',NULL,'{\"budget\": \"$10000.0\", \"phases\": [{\"phase\": \"1. Research and Planning\", \"duration\": \"4 weeks\", \"milestones\": [\"Define marketing objectives\", \"Identify target audience\", \"Conduct market research\", \"Develop marketing strategy\"], \"deliverables\": [\"Marketing objectives\", \"Target audience profile\", \"Market research report\", \"Marketing strategy\"]}, {\"phase\": \"2. Creative Development\", \"duration\": \"3 weeks\", \"milestones\": [\"Create campaign concept\", \"Develop campaign materials\", \"Review and revise campaign materials\"], \"deliverables\": [\"Campaign concept\", \"Campaign materials\"]}, {\"phase\": \"3. Campaign Execution\", \"duration\": \"6 weeks\", \"milestones\": [\"Launch marketing campaign\", \"Monitor campaign progress\", \"Adjust campaign as needed\"], \"deliverables\": [\"Launched campaign\", \"Campaign progress report\"]}, {\"phase\": \"4. Evaluation and Reporting\", \"duration\": \"2 weeks\", \"milestones\": [\"Collect campaign results\", \"Analyze campaign performance\", \"Create campaign report\"], \"deliverables\": [\"Campaign results\", \"Campaign performance analysis\", \"Final campaign report\"]}], \"project\": \"Marketing Campaign\"}',NULL,'draft',NULL,'2025-11-13 12:36:51','2025-11-13 12:36:51',1,'professional',NULL,NULL,NULL,NULL),(10,2,1,'E-commerce',1000.00,'Low Website click','Girls','{\"seo\": true, \"email\": false, \"website\": true, \"youtube\": true, \"facebook\": true, \"linkedin\": true, \"instagram\": true, \"google_ads\": false}',NULL,'{\"Budget\": \"$1000.0\", \"Company\": \"hashnate\", \"Challenges\": \"Low Website click\", \"Business_Type\": \"E-commerce\", \"Target_Audience\": \"Girls\", \"Automation_Tools\": [{\"tool\": \"MailChimp\", \"use_case\": \"Email marketing automation\"}, {\"tool\": \"Hootsuite\", \"use_case\": \"Social media scheduling and management\"}, {\"tool\": \"SEMrush\", \"use_case\": \"SEO and content marketing\"}, {\"tool\": \"AdEspresso\", \"use_case\": \"Google Ads management\"}], \"Existing_Presence\": {\"seo\": true, \"email\": false, \"website\": true, \"youtube\": true, \"facebook\": true, \"linkedin\": true, \"instagram\": true, \"google_ads\": false}, \"Recommended_Campaigns\": [{\"platform\": \"Website\", \"campaign_type\": \"SEO\", \"content_topics\": \"Fashion, Beauty, Lifestyle, DIY projects\", \"creative_formats\": \"Blog posts\"}, {\"platform\": \"Instagram, Facebook, YouTube\", \"campaign_type\": \"Social Media\", \"content_topics\": \"Fashion trends, Beauty tips, Lifestyle inspiration, DIY tutorials\", \"creative_formats\": \"Photos, Videos, Stories, Live sessions\"}, {\"platform\": \"Google\", \"campaign_type\": \"Google Ads\", \"content_topics\": \"Product promotions, Seasonal sales\", \"creative_formats\": \"Display ads, Shopping ads\"}, {\"platform\": \"Email\", \"campaign_type\": \"Email\", \"content_topics\": \"Exclusive offers, New arrivals, Customer testimonials\", \"creative_formats\": \"Newsletters, Promotional emails\"}], \"Platform_Recommendations\": [{\"reason\": \"High engagement rate among target audience\", \"platform\": \"Instagram\"}, {\"reason\": \"Wide reach and targeted advertising options\", \"platform\": \"Facebook\"}, {\"reason\": \"Video content is popular and engaging\", \"platform\": \"YouTube\"}, {\"reason\": \"Direct communication with customers for personalized offers\", \"platform\": \"Email\"}, {\"reason\": \"Increase website traffic and visibility\", \"platform\": \"Google Ads\"}]}',NULL,'{\"differentiators\": [{\"title\": \"Faster deployment with automation\", \"impact\": \"This means you can go live with your campaigns faster, react to market changes in real-time, and capitalize on opportunities quicker than your competitors.\", \"description\": \"Our digital marketing agency leverages cutting-edge automation tools to implement marketing strategies at a quicker pace, saving your time and resources.\"}, {\"title\": \"AI-personalized targeting\", \"impact\": \"With AI-personalized targeting, you can expect higher engagement rates, increased customer loyalty, and ultimately, more conversions and sales.\", \"description\": \"We use advanced AI algorithms to analyze customer behavior, preferences, and trends. This enables us to craft highly personalized marketing campaigns that resonate with your target audience.\"}, {\"title\": \"Cost-efficiency\", \"impact\": \"This ensures that every dollar you spend contributes directly to your bottom line, giving you more value for your marketing budget.\", \"description\": \"Our digital marketing solutions are designed to maximize your return on investment. We focus on cost-effective strategies that drive tangible results, not just vanity metrics.\"}, {\"title\": \"Advanced performance tracking\", \"impact\": \"With advanced performance tracking, you can continuously optimize your marketing strategies, improve your ROI, and stay ahead of your competition.\", \"description\": \"We offer comprehensive performance tracking and reporting. Our advanced analytics tools provide real-time insights into your campaigns\' performance, helping you make data-driven decisions.\"}]}',NULL,'{\"project\": {\"budget\": \"$1000.0\", \"phases\": [{\"phase\": \"1. Market Research\", \"duration\": \"2 weeks\", \"milestones\": [\"Identify target audience\", \"Analyze competitors\", \"Identify marketing channels\"], \"deliverables\": [\"Market research report\", \"Target audience profile\", \"Competitor analysis report\"]}, {\"phase\": \"2. Strategy Development\", \"duration\": \"2 weeks\", \"milestones\": [\"Define marketing goals\", \"Develop marketing strategies\", \"Identify key performance indicators\"], \"deliverables\": [\"Marketing strategy document\", \"Marketing goals and KPIs\"]}, {\"phase\": \"3. Content Creation\", \"duration\": \"3 weeks\", \"milestones\": [\"Develop content calendar\", \"Create marketing content\", \"Prepare marketing materials\"], \"deliverables\": [\"Content calendar\", \"Marketing content\", \"Marketing materials\"]}, {\"phase\": \"4. Campaign Launch\", \"duration\": \"1 week\", \"milestones\": [\"Launch marketing campaign\", \"Monitor initial campaign performance\"], \"deliverables\": [\"Launched marketing campaign\", \"Initial campaign performance report\"]}, {\"phase\": \"5. Campaign Monitoring and Adjustment\", \"duration\": \"4 weeks\", \"milestones\": [\"Analyze campaign performance\", \"Make necessary campaign adjustments\", \"Track KPIs\"], \"deliverables\": [\"Ongoing campaign performance reports\", \"Adjusted marketing campaign\"]}, {\"phase\": \"6. Campaign Evaluation\", \"duration\": \"2 weeks\", \"milestones\": [\"Evaluate overall campaign performance\", \"Assess achievement of marketing goals\", \"Prepare final campaign report\"], \"deliverables\": [\"Final campaign performance report\", \"Marketing goals achievement report\"]}]}}',NULL,'draft',NULL,'2025-11-13 14:27:55','2025-11-13 14:27:55',1,'professional',NULL,NULL,NULL,NULL),(11,7,1,'Restaurant',1550.00,'low website traffic','Girls','{\"seo\": false, \"email\": false, \"website\": true, \"youtube\": true, \"facebook\": true, \"linkedin\": true, \"instagram\": true, \"google_ads\": false}',NULL,'{\"budget\": 1550.0, \"company\": \"hashnate\", \"challenges\": \"low website traffic\", \"business_type\": \"Restaurant\", \"target_audience\": \"Girls\", \"automation_tools\": [{\"tool\": \"Hootsuite\", \"purpose\": \"To schedule and manage social media posts\"}, {\"tool\": \"Google Analytics\", \"purpose\": \"To track website traffic and user behavior\"}, {\"tool\": \"Mailchimp\", \"purpose\": \"To manage email marketing campaigns\"}, {\"tool\": \"SEMRush\", \"purpose\": \"To optimize SEO efforts\"}], \"existing_presence\": {\"seo\": false, \"email\": false, \"website\": true, \"youtube\": true, \"facebook\": true, \"linkedin\": true, \"instagram\": true, \"google_ads\": false}, \"recommended_campaigns\": [{\"type\": \"ad\", \"platforms\": [\"google_ads\", \"facebook\"], \"content_topic\": \"Promotion of restaurant special deals and menu items\", \"creative_format\": \"video\", \"budget_allocation\": \"30%\"}, {\"type\": \"email\", \"platform\": \"mailchimp\", \"content_topic\": \"New menu items, special deals and events\", \"creative_format\": \"newsletter\", \"budget_allocation\": \"20%\"}, {\"type\": \"SEO\", \"platform\": \"website\", \"content_topic\": \"Restaurant experience, menu items, chef profiles\", \"creative_format\": \"blog posts\", \"budget_allocation\": \"20%\"}, {\"type\": \"social_media\", \"platforms\": [\"instagram\", \"facebook\", \"youtube\"], \"content_topic\": \"Behind the scenes, menu items, customer experiences\", \"creative_format\": \"images and short videos\", \"budget_allocation\": \"30%\"}]}',NULL,'{\"differentiators\": [{\"title\": \"Faster Deployment with Automation\", \"impact\": \"This allows your restaurant to be more responsive to market changes and to take advantage of opportunities as they arise.\", \"description\": \"We leverage cutting-edge automation tools to speed up your marketing campaigns. This means less waiting time and quicker results.\"}, {\"title\": \"AI-Personalized Targeting\", \"impact\": \"By personalizing your marketing, you can increase customer engagement and loyalty, leading to higher sales and revenue.\", \"description\": \"Our agency uses advanced AI technology to personalize your marketing campaigns. This means your ads will be more relevant to each individual customer.\"}, {\"title\": \"Cost-Efficiency\", \"impact\": \"This means you can allocate more of your budget to other important areas of your restaurant business, like improving the menu or enhancing the dining experience.\", \"description\": \"We strive to give you the best return on your investment. Our strategies are designed to maximize results while minimizing costs.\"}, {\"title\": \"Advanced Performance Tracking\", \"impact\": \"With this information, you can make data-driven decisions and continuously improve your marketing strategies.\", \"description\": \"We provide comprehensive performance tracking for all your marketing campaigns. This includes detailed analytics and reports that show you exactly how your marketing efforts are performing.\"}]}',NULL,'{\"phases\": [{\"duration\": \"2 weeks\", \"milestones\": [\"Market Research Completed\", \"SWOT Analysis Completed\", \"Marketing Objectives Defined\"], \"phase_name\": \"Research and Planning\", \"deliverables\": [\"Detailed Market Research Report\", \"SWOT Analysis Report\", \"Marketing Objectives Document\"]}, {\"duration\": \"3 weeks\", \"milestones\": [\"Marketing Strategy Defined\", \"Marketing Mix Decided\", \"Budget Allocation Completed\"], \"phase_name\": \"Strategy Development\", \"deliverables\": [\"Marketing Strategy Document\", \"Marketing Mix Report\", \"Budget Allocation Report\"]}, {\"duration\": \"4 weeks\", \"milestones\": [\"Creative Concepts Developed\", \"Marketing Materials Designed\", \"Marketing Message Finalized\"], \"phase_name\": \"Creative Development\", \"deliverables\": [\"Creative Concepts Document\", \"Marketing Materials\", \"Marketing Message Document\"]}, {\"duration\": \"6 weeks\", \"milestones\": [\"Marketing Channels Identified\", \"Marketing Campaign Launched\", \"Monitoring and Tracking System Set Up\"], \"phase_name\": \"Implementation\", \"deliverables\": [\"Marketing Channels Report\", \"Marketing Campaign Launch Report\", \"Monitoring and Tracking System Report\"]}, {\"duration\": \"4 weeks\", \"milestones\": [\"Campaign Performance Monitored\", \"Marketing Results Evaluated\", \"Improvements Identified\"], \"phase_name\": \"Monitoring and Evaluation\", \"deliverables\": [\"Campaign Performance Report\", \"Marketing Results Report\", \"Improvements Document\"]}], \"project_budget\": \"$1550.0\"}',NULL,'draft',NULL,'2025-11-14 05:46:37','2025-11-14 05:46:37',1,'professional',NULL,NULL,NULL,NULL),(12,12,1,'Hospitality',4000.00,'Locw click rate','children','{\"seo\": true, \"email\": false, \"website\": true, \"youtube\": true, \"facebook\": true, \"linkedin\": true, \"instagram\": true, \"google_ads\": true}',NULL,'{\"Budget\": \"$4000.0\", \"Company\": \"hashnate\", \"Challenges\": \"Low click rate\", \"Business Type\": \"Hospitality\", \"Content Topics\": [\"Interactive Games\", \"Fun Activities\", \"Photo Contest\", \"Educational Fun\", \"Cartoon Explainers\"], \"Target Audience\": \"children\", \"Automation Tools\": [{\"name\": \"Hootsuite\", \"purpose\": \"To manage and schedule social media posts\"}, {\"name\": \"SEMRush\", \"purpose\": \"For SEO optimization and tracking\"}, {\"name\": \"Google Ads automation\", \"purpose\": \"For managing and optimizing Google Ads\"}, {\"name\": \"MailChimp\", \"purpose\": \"For email marketing automation once email is active\"}], \"Creative Formats\": [\"Interactive ad\", \"Video ad\", \"Photo ad\", \"Blog post\", \"Animated video\"], \"Existing Presence\": {\"seo\": true, \"email\": false, \"website\": true, \"youtube\": true, \"facebook\": true, \"linkedin\": true, \"instagram\": true, \"google_ads\": true}, \"Recommended Campaigns\": [{\"goal\": \"Increase click rate\", \"type\": \"Ad\", \"platform\": \"Google Ads\", \"content_topic\": \"Interactive Games\", \"creative_format\": \"Interactive ad\", \"budget_allocation\": \"30%\"}, {\"goal\": \"Increase engagement\", \"type\": \"Social Media\", \"platform\": \"Facebook\", \"content_topic\": \"Fun Activities\", \"creative_format\": \"Video ad\", \"budget_allocation\": \"25%\"}, {\"goal\": \"Increase user-generated content\", \"type\": \"Social Media\", \"platform\": \"Instagram\", \"content_topic\": \"Photo Contest\", \"creative_format\": \"Photo ad\", \"budget_allocation\": \"15%\"}, {\"goal\": \"Increase organic traffic\", \"type\": \"SEO\", \"platform\": \"Website\", \"content_topic\": \"Educational Fun\", \"creative_format\": \"Blog post\", \"budget_allocation\": \"15%\"}, {\"goal\": \"Increase brand awareness\", \"type\": \"Video\", \"platform\": \"YouTube\", \"content_topic\": \"Cartoon Explainers\", \"creative_format\": \"Animated video\", \"budget_allocation\": \"15%\"}], \"Platform Recommendations\": [\"Google Ads\", \"Facebook\", \"Instagram\", \"Website SEO\", \"YouTube\"]}','<h1 class=\"ql-align-center\">Digital Marketing Proposal</h1><h2 class=\"ql-align-center\">for hashnate</h2><p class=\"ql-align-center\"><em>Prepared by PanvelIQ</em></p><h2><strong>Executive Summary</strong></h2><p>This comprehensive digital marketing proposal has been specifically designed for <strong>hashnate</strong>, a Hospitality looking to enhance their digital presence and drive measurable growth.</p><p>Our AI-powered approach combines cutting-edge marketing technology with proven strategies to deliver exceptional results within your investment budget of <strong>$4,000</strong>.</p><h2><strong>Current Challenges</strong></h2><p>Locw click rate</p><h2><strong>Target Audience Analysis</strong></h2><p>children</p><h2><strong>Recommended Marketing Strategy</strong></h2><p>Based on our AI analysis, we recommend a comprehensive marketing approach across multiple channels.</p><h3><strong>Recommended Campaigns</strong></h3><ul><li>AI-powered digital marketing campaigns tailored to your business needs</li></ul><h3><strong>Automation Tools &amp; Technologies</strong></h3><ul><li>Marketing automation and analytics tools</li></ul><h2><strong>Competitive Differentiators</strong></h2><p>What sets our approach apart:</p><ul><li><strong>Faster Deployment with Automation:</strong> Using our advanced automation tools, we ensure your campaigns are launched quickly and efficiently. This not only saves time but also helps in reaching your target audience faster.</li><li><em>Impact: This leads to quicker results and higher ROI for your marketing efforts.</em></li><li><strong>AI-Personalized Targeting:</strong> We use AI-powered algorithms to personalize your campaigns based on the behavior and preferences of your target audience. This ensures your messages resonate with your audience and lead to more conversions.</li><li><em>Impact: This significantly increases engagement rates and conversions, leading to higher profits.</em></li><li><strong>Cost-Efficiency:</strong> Our digital marketing solutions are designed to maximize the use of your budget. We ensure every dollar spent gives you the highest possible return.</li><li><em>Impact: This results in lower cost per acquisition and higher ROI.</em></li><li><strong>Advanced Performance Tracking:</strong> We provide real-time performance tracking of your campaigns. This allows you to make data-driven decisions and optimize your campaigns based on what\'s working best.</li><li><em>Impact: This leads to continuous improvement of your campaigns and maximized results.</em></li></ul><h2><strong>Project Timeline</strong></h2><h3><strong>Phase 1: 1. Research &amp; Planning</strong></h3><p><strong>Duration:</strong> 2 weeks</p><p><strong>Key Deliverables:</strong></p><ul><li>Marketing strategy document</li><li>Target audience profile</li><li>Competitor analysis report</li></ul><h3><strong>Phase 2: 2. Creative Development</strong></h3><p><strong>Duration:</strong> 3 weeks</p><p><strong>Key Deliverables:</strong></p><ul><li>Marketing creatives</li><li>Copywriting drafts</li><li>Finalized designs</li></ul><h3><strong>Phase 3: 3. Campaign Setup</strong></h3><p><strong>Duration:</strong> 1 week</p><p><strong>Key Deliverables:</strong></p><ul><li>Ready to launch campaigns</li><li>Test run reports</li></ul><h3><strong>Phase 4: 4. Campaign Launch</strong></h3><p><strong>Duration:</strong> 1 week</p><p><strong>Key Deliverables:</strong></p><ul><li>Launched campaign</li><li>Initial performance report</li></ul><h3><strong>Phase 5: 5. Campaign Monitoring &amp; Optimization</strong></h3><p><strong>Duration:</strong> 4 weeks</p><p><strong>Key Deliverables:</strong></p><ul><li>Weekly performance reports</li><li>Optimized campaigns</li></ul><h3><strong>Phase 6: 6. Reporting &amp; Analysis</strong></h3><p><strong>Duration:</strong> 2 weeks</p><p><strong>Key Deliverables:</strong></p><ul><li>Final marketing report</li><li>Data analysis</li><li>Learnings and recommendations</li></ul><h2><strong>Investment &amp; ROI</strong></h2><p><strong>Total Investment:</strong> $4,000</p><p>Our data-driven approach ensures maximum return on investment through:</p><ul><li>Continuous performance optimization</li><li>AI-powered audience targeting</li><li>Real-time analytics and reporting</li><li>Agile campaign management</li></ul><h2><strong>Next Steps</strong></h2><ol><li>Review this proposal and provide feedback</li><li>Schedule a strategy session to discuss implementation</li><li>Finalize project scope and timeline</li><li>Begin Phase 1 execution</li></ol><p class=\"ql-align-center\"><strong>We look forward to partnering with you to achieve exceptional marketing results!</strong></p><p class=\"ql-align-center\"><em>Contact: info@panveliq.com | www.panveliq.com</em></p>','{\"differentiators\": [{\"title\": \"Faster Deployment with Automation\", \"impact\": \"This leads to quicker results and higher ROI for your marketing efforts.\", \"description\": \"Using our advanced automation tools, we ensure your campaigns are launched quickly and efficiently. This not only saves time but also helps in reaching your target audience faster.\"}, {\"title\": \"AI-Personalized Targeting\", \"impact\": \"This significantly increases engagement rates and conversions, leading to higher profits.\", \"description\": \"We use AI-powered algorithms to personalize your campaigns based on the behavior and preferences of your target audience. This ensures your messages resonate with your audience and lead to more conversions.\"}, {\"title\": \"Cost-Efficiency\", \"impact\": \"This results in lower cost per acquisition and higher ROI.\", \"description\": \"Our digital marketing solutions are designed to maximize the use of your budget. We ensure every dollar spent gives you the highest possible return.\"}, {\"title\": \"Advanced Performance Tracking\", \"impact\": \"This leads to continuous improvement of your campaigns and maximized results.\", \"description\": \"We provide real-time performance tracking of your campaigns. This allows you to make data-driven decisions and optimize your campaigns based on what\'s working best.\"}]}',NULL,'{\"budget\": \"$4000.0\", \"phases\": [{\"phase\": \"1. Research & Planning\", \"duration\": \"2 weeks\", \"milestones\": [\"Identify target audience\", \"Competitor analysis\", \"Define marketing objectives\"], \"deliverables\": [\"Marketing strategy document\", \"Target audience profile\", \"Competitor analysis report\"]}, {\"phase\": \"2. Creative Development\", \"duration\": \"3 weeks\", \"milestones\": [\"Concept development\", \"Copywriting\", \"Design\"], \"deliverables\": [\"Marketing creatives\", \"Copywriting drafts\", \"Finalized designs\"]}, {\"phase\": \"3. Campaign Setup\", \"duration\": \"1 week\", \"milestones\": [\"Campaign setup on chosen platforms\", \"Test runs\"], \"deliverables\": [\"Ready to launch campaigns\", \"Test run reports\"]}, {\"phase\": \"4. Campaign Launch\", \"duration\": \"1 week\", \"milestones\": [\"Campaign launch\", \"Monitoring initial performance\"], \"deliverables\": [\"Launched campaign\", \"Initial performance report\"]}, {\"phase\": \"5. Campaign Monitoring & Optimization\", \"duration\": \"4 weeks\", \"milestones\": [\"Weekly performance analysis\", \"Optimization\"], \"deliverables\": [\"Weekly performance reports\", \"Optimized campaigns\"]}, {\"phase\": \"6. Reporting & Analysis\", \"duration\": \"2 weeks\", \"milestones\": [\"Data collection\", \"Analysis\", \"Final report preparation\"], \"deliverables\": [\"Final marketing report\", \"Data analysis\", \"Learnings and recommendations\"]}], \"project\": \"Marketing Campaign\"}',NULL,'draft',NULL,'2025-11-14 05:56:10','2025-11-14 11:32:02',1,'professional',NULL,NULL,NULL,NULL),(13,13,1,'Retail',3000.00,'Low click rates and low website traffic','Everyone','{\"seo\": true, \"email\": false, \"website\": true, \"youtube\": true, \"facebook\": true, \"linkedin\": true, \"instagram\": true, \"google_ads\": true}',NULL,'{\"Budget\": 3000.0, \"Company\": \"hashnate\", \"Challenges\": [\"Low click rates\", \"low website traffic\"], \"Business_Type\": \"Retail\", \"Target_Audience\": \"Everyone\", \"Automation_Tools\": [{\"Tool\": \"MailChimp\", \"Purpose\": \"Email Marketing Automation\", \"Budget_Allocation_Percentage\": 5}, {\"Tool\": \"Hootsuite\", \"Purpose\": \"Social Media Management\", \"Budget_Allocation_Percentage\": 5}, {\"Tool\": \"SEMRush\", \"Purpose\": \"SEO and Content Marketing\", \"Budget_Allocation_Percentage\": 5}, {\"Tool\": \"Google Ads\", \"Purpose\": \"PPC Management\", \"Budget_Allocation_Percentage\": 5}], \"Existing_Presence\": {\"seo\": true, \"email\": false, \"website\": true, \"youtube\": true, \"facebook\": true, \"linkedin\": true, \"instagram\": true, \"google_ads\": true}, \"Recommended_Campaigns\": [{\"Type\": \"Ad\", \"Platform\": \"Google Ads\", \"Content_Topics\": [\"Product Features\", \"Discounts\", \"Customer Reviews\"], \"Creative_Formats\": [\"Image Ads\", \"Video Ads\", \"Carousel Ads\"], \"Budget_Allocation_Percentage\": 35}, {\"Type\": \"SEO\", \"Platform\": \"Website\", \"Content_Topics\": [\"Product Descriptions\", \"Blog Posts on Relevant Topics\", \"FAQ\"], \"Creative_Formats\": [\"Text Content\", \"Infographics\"], \"Budget_Allocation_Percentage\": 25}, {\"Type\": \"Social Media\", \"Platform\": [\"Facebook\", \"Instagram\", \"LinkedIn\"], \"Content_Topics\": [\"Brand Story\", \"Behind-the-Scenes\", \"Customer Testimonials\"], \"Creative_Formats\": [\"Short Videos\", \"Images\", \"Stories\"], \"Budget_Allocation_Percentage\": 30}, {\"Type\": \"Email\", \"Platform\": \"Email Service Provider\", \"Content_Topics\": [\"Product Updates\", \"Special Offers\", \"Newsletters\"], \"Creative_Formats\": [\"HTML Emails\", \"Plain Text Emails\"], \"Budget_Allocation_Percentage\": 10}]}','<h1 class=\"ql-align-center\"><span class=\"ql-size-large\">Digital Marketing Proposal</span></h1><p class=\"ql-align-center\"><br></p><h2 class=\"ql-align-center\">for hashnate software Engineering</h2><p class=\"ql-align-center\"><em>Prepared by PanvelIQ</em></p><h2><strong>Executive Summary</strong></h2><p>This comprehensive digital marketing proposal has been specifically designed for <strong>hashnate</strong>, a Retail looking to enhance their digital presence and drive measurable growth.</p><p>Our AI-powered approach combines cutting-edge marketing technology with proven strategies to deliver exceptional results within your investment budget of <strong>$3,000</strong>.</p><h2><strong>Current Challenges</strong></h2><p>Low click rates and low website traffic</p><h2><strong>Target Audience Analysis</strong></h2><p>Everyone</p><h2><strong>Recommended Marketing Strategy</strong></h2><p>Based on our AI analysis, we recommend a comprehensive marketing approach across multiple channels.</p><h3><strong>Recommended Campaigns</strong></h3><ul><li><strong>Ad</strong> (Google Ads): Product Features, Discounts, Customer Reviews <em>(35% of budget)</em></li><li><strong>SEO</strong> (Website): Product Descriptions, Blog Posts on Relevant Topics, FAQ <em>(25% of budget)</em></li><li><strong>Social Media</strong> (Facebook, Instagram, LinkedIn): Brand Story, Behind-the-Scenes, Customer Testimonials <em>(30% of budget)</em></li><li><strong>Email</strong> (Email Service Provider): Product Updates, Special Offers, Newsletters <em>(10% of budget)</em></li></ul><h3><strong>Automation Tools &amp; Technologies</strong></h3><ul><li><strong>MailChimp:</strong> Email Marketing Automation <em>(5% of budget)</em></li><li><strong>Hootsuite:</strong> Social Media Management <em>(5% of budget)</em></li><li><strong>SEMRush:</strong> SEO and Content Marketing <em>(5% of budget)</em></li><li><strong>Google Ads:</strong> PPC Management <em>(5% of budget)</em></li></ul><h2><strong>Competitive Differentiators</strong></h2><p>What sets our approach apart:</p><ul><li><strong>Faster Deployment with Automation:</strong> Our digital marketing agency leverages advanced automation tools to streamline the execution of your marketing campaigns. This enables us to deploy your campaigns swiftly and efficiently, reducing time-to-market.</li><li><em>Impact: This will allow you to engage with your target audience in a timely manner, capitalizing on market trends and opportunities as they emerge.</em></li><li><strong>AI-Personalized Targeting:</strong> We utilize Artificial Intelligence (AI) to personalize your marketing messages based on the preferences and behaviors of your target audience. This ensures that each communication is tailored to resonate with its recipient.</li><li><em>Impact: This will significantly boost your engagement rates, conversion rates, and ultimately, your return on investment.</em></li><li><strong>Cost-Efficiency:</strong> Our agency prides itself on delivering high-quality digital marketing services at an affordable price. We optimize your marketing budget to ensure maximum impact and return on investment.</li><li><em>Impact: This will allow you to achieve your marketing objectives without straining your finances.</em></li><li><strong>Advanced Performance Tracking:</strong> We provide advanced performance tracking capabilities that allow you to monitor the effectiveness of your marketing campaigns in real-time. Our comprehensive reports include deep insights and actionable recommendations.</li><li><em>Impact: This will empower you to make informed decisions and continuously improve your marketing strategy.</em></li></ul><h2><strong>Project Timeline</strong></h2><h3><strong>Phase 1: 1. Market Research</strong></h3><p><strong>Duration:</strong> 2 weeks</p><p><strong>Key Deliverables:</strong></p><ul><li>Market research report</li><li>Customer profile</li></ul><h3><strong>Phase 2: 2. Marketing Strategy Development</strong></h3><p><strong>Duration:</strong> 3 weeks</p><p><strong>Key Deliverables:</strong></p><ul><li>Marketing strategy document</li><li>Marketing budget breakdown</li></ul><h3><strong>Phase 3: 3. Creative Development</strong></h3><p><strong>Duration:</strong> 2 weeks</p><p><strong>Key Deliverables:</strong></p><ul><li>Marketing materials</li><li>Marketing messages document</li></ul><h3><strong>Phase 4: 4. Marketing Execution</strong></h3><p><strong>Duration:</strong> 4 weeks</p><p><strong>Key Deliverables:</strong></p><ul><li>Marketing execution report</li><li>Adjusted marketing plan</li></ul><h3><strong>Phase 5: 5. Analysis and Reporting</strong></h3><p><strong>Duration:</strong> 2 weeks</p><p><strong>Key Deliverables:</strong></p><ul><li>Marketing analysis report</li><li>Final marketing presentation</li></ul><p><br></p><h2><strong>Investment &amp; ROI</strong></h2><p><strong>Total Investment:</strong> $3,000</p><p>Our data-driven approach ensures maximum return on investment through:</p><ul><li>Continuous performance optimization</li><li>AI-powered audience targeting</li><li>Real-time analytics and reporting</li><li>Agile campaign management</li></ul><h2><strong>Next Steps</strong></h2><ol><li>Review this proposal and provide feedback</li><li>Schedule a strategy session to discuss implementation</li><li>Finalize project scope and timeline</li><li>Begin Phase 1 execution</li></ol><p><br></p><p><br></p><p><br></p><p><br></p><p><br></p><p class=\"ql-align-center\">======================================</p><p class=\"ql-align-center\"><strong>We look forward to partnering with you to achieve exceptional marketing results!</strong></p><p class=\"ql-align-center\"><em>Contact: info@panveliq.com | www.panveliq.com</em></p>','{\"differentiators\": [{\"title\": \"Faster Deployment with Automation\", \"impact\": \"This will allow you to engage with your target audience in a timely manner, capitalizing on market trends and opportunities as they emerge.\", \"description\": \"Our digital marketing agency leverages advanced automation tools to streamline the execution of your marketing campaigns. This enables us to deploy your campaigns swiftly and efficiently, reducing time-to-market.\"}, {\"title\": \"AI-Personalized Targeting\", \"impact\": \"This will significantly boost your engagement rates, conversion rates, and ultimately, your return on investment.\", \"description\": \"We utilize Artificial Intelligence (AI) to personalize your marketing messages based on the preferences and behaviors of your target audience. This ensures that each communication is tailored to resonate with its recipient.\"}, {\"title\": \"Cost-Efficiency\", \"impact\": \"This will allow you to achieve your marketing objectives without straining your finances.\", \"description\": \"Our agency prides itself on delivering high-quality digital marketing services at an affordable price. We optimize your marketing budget to ensure maximum impact and return on investment.\"}, {\"title\": \"Advanced Performance Tracking\", \"impact\": \"This will empower you to make informed decisions and continuously improve your marketing strategy.\", \"description\": \"We provide advanced performance tracking capabilities that allow you to monitor the effectiveness of your marketing campaigns in real-time. Our comprehensive reports include deep insights and actionable recommendations.\"}]}',NULL,'{\"budget\": \"$3000.0\", \"phases\": [{\"phase\": \"1. Market Research\", \"duration\": \"2 weeks\", \"milestones\": [\"Identify target market\", \"Competitor analysis\", \"Customer needs assessment\"], \"deliverables\": [\"Market research report\", \"Customer profile\"]}, {\"phase\": \"2. Marketing Strategy Development\", \"duration\": \"3 weeks\", \"milestones\": [\"Develop marketing goals\", \"Identify marketing tactics\", \"Create marketing budget\"], \"deliverables\": [\"Marketing strategy document\", \"Marketing budget breakdown\"]}, {\"phase\": \"3. Creative Development\", \"duration\": \"2 weeks\", \"milestones\": [\"Develop creative concepts\", \"Create marketing messages\", \"Design marketing materials\"], \"deliverables\": [\"Marketing materials\", \"Marketing messages document\"]}, {\"phase\": \"4. Marketing Execution\", \"duration\": \"4 weeks\", \"milestones\": [\"Implement marketing tactics\", \"Monitor marketing activities\", \"Adjust marketing tactics as needed\"], \"deliverables\": [\"Marketing execution report\", \"Adjusted marketing plan\"]}, {\"phase\": \"5. Analysis and Reporting\", \"duration\": \"2 weeks\", \"milestones\": [\"Analyze marketing results\", \"Create marketing report\", \"Present marketing results\"], \"deliverables\": [\"Marketing analysis report\", \"Final marketing presentation\"]}], \"project\": \"Marketing Project\"}',NULL,'draft',NULL,'2025-11-14 06:25:39','2025-11-14 11:10:22',1,'professional',NULL,NULL,NULL,'hashnate'),(14,14,1,'E-commerce',1000.00,'Low website and post click rate','Children and Girls','{\"seo\": false, \"email\": false, \"website\": true, \"youtube\": true, \"facebook\": true, \"linkedin\": true, \"instagram\": true, \"google_ads\": true}',NULL,'{\"budget\": \"$1000.0\", \"company\": \"CALIM\", \"challenges\": \"Low website and post click rate\", \"business_type\": \"E-commerce\", \"target_audience\": \"Children and Girls\", \"automation_tools\": [{\"purpose\": \"To track and measure website traffic, analyze user behavior\", \"tool_name\": \"Google Analytics\"}, {\"purpose\": \"To schedule and automate social media posts, track engagement\", \"tool_name\": \"Hootsuite\"}, {\"purpose\": \"To optimize SEO, track keyword rankings, analyze website\", \"tool_name\": \"SEMRush\"}, {\"purpose\": \"To automate email marketing campaigns, track email open rates and CTR\", \"tool_name\": \"MailChimp\"}], \"existing_presence\": {\"seo\": false, \"email\": false, \"website\": true, \"youtube\": true, \"facebook\": true, \"linkedin\": true, \"instagram\": true, \"google_ads\": true}, \"recommended_campaigns\": [{\"campaign_type\": \"Google Ads\", \"content_topics\": \"Toy Reviews, New Arrivals, Seasonal Offers\", \"target_audience\": \"Children and Girls\", \"creative_formats\": \"Product Images, Short Videos\", \"budget_allocation_percentage\": \"30%\"}, {\"campaign_type\": \"Social Media (Facebook, Instagram)\", \"content_topics\": \"Customer Testimonials, DIY Toy Ideas, Trending Toys\", \"target_audience\": \"Children and Girls\", \"creative_formats\": \"Carousel Ads (Product Images), Story Ads (Short Videos)\", \"budget_allocation_percentage\": \"40%\"}, {\"campaign_type\": \"YouTube\", \"content_topics\": \"Toy Reviews, DIY Toy Ideas\", \"target_audience\": \"Children and Girls\", \"creative_formats\": \"Product Review Videos, Unboxing Videos\", \"budget_allocation_percentage\": \"20%\"}, {\"campaign_type\": \"SEO\", \"content_topics\": \"Toy Reviews, Latest Toy Trends, DIY Toy Ideas\", \"target_audience\": \"Children and Girls\", \"creative_formats\": \"Keyword Rich Blog Posts\", \"budget_allocation_percentage\": \"10%\"}]}','<h1 class=\"ql-align-center\">Digital Marketing Proposal</h1><h2 class=\"ql-align-center\">for CALIM</h2><p class=\"ql-align-center\"><em>Prepared by PanvelIQ</em></p><h2><strong>Executive Summary</strong></h2><p>This comprehensive digital marketing proposal has been specifically designed for <strong>CALIM</strong>, a E-commerce looking to enhance their digital presence and drive measurable growth.</p><p>Our AI-powered approach combines cutting-edge marketing technology with proven strategies to deliver exceptional results within your investment budget of <strong>$1,000</strong>.</p><h2><strong>Current Challenges</strong></h2><p>Low website and post click rate</p><h2><strong>Target Audience Analysis</strong></h2><p>Children and Girls</p><h2><strong>Recommended Marketing Strategy</strong></h2><p>Based on our AI analysis, we recommend a comprehensive marketing approach across multiple channels.</p><h3><strong>Recommended Campaigns</strong></h3><ul><li>AI-powered digital marketing campaigns tailored to your business needs</li></ul><h3><strong>Automation Tools &amp; Technologies</strong></h3><ul><li><strong>Marketing Tool:</strong> To track and measure website traffic, analyze user behavior</li><li><strong>Marketing Tool:</strong> To schedule and automate social media posts, track engagement</li><li><strong>Marketing Tool:</strong> To optimize SEO, track keyword rankings, analyze website</li><li><strong>Marketing Tool:</strong> To automate email marketing campaigns, track email open rates and CTR</li></ul><h2><strong>Competitive Differentiators</strong></h2><p>What sets our approach apart:</p><ul><li><strong>AI-Powered Approach:</strong> Leveraging cutting-edge technology for optimal results</li><li><em>Impact: Increased efficiency and ROI</em></li></ul><h2><strong>Project Timeline</strong></h2><h3><strong>Phase 1: Planning &amp; Setup</strong></h3><p><strong>Duration:</strong> 2-4 weeks</p><ul><li>Initial strategy development</li></ul><p><br></p><h2><strong>Investment &amp; ROI</strong></h2><p><strong>Total Investment:</strong> $1,000</p><p>Our data-driven approach ensures maximum return on investment through:</p><ul><li>Continuous performance optimization</li><li>AI-powered audience targeting</li><li>Real-time analytics and reporting</li><li>Agile campaign management</li></ul><h2><strong>Next Steps</strong></h2><ol><li>Review this proposal and provide feedback</li><li>Schedule a strategy session to discuss implementation</li><li>Finalize project scope and timeline</li><li>Begin Phase 1 execution</li></ol><p><br></p><p><br></p><p><br></p><p><br></p><p><br></p><p><br></p><p class=\"ql-align-center\"><strong>We look forward to partnering with you to achieve exceptional marketing results!</strong></p><p class=\"ql-align-center\"><em>Contact: info@panveliq.com | www.panveliq.com</em></p>','{\"competitive_differentiators\": [{\"title\": \"Faster Deployment with Automation\", \"impact\": \"This ensures that your e-commerce business can quickly react to market changes, thus providing a competitive edge.\", \"description\": \"Our digital marketing agency leverages advanced automation tools to streamline marketing processes, enabling faster deployment of campaigns.\"}, {\"title\": \"AI-Personalized Targeting\", \"impact\": \"This leads to more effective targeting, improved customer engagement, and increased conversion rates.\", \"description\": \"We utilize AI technology to analyze customer behavior and create personalized marketing strategies.\"}, {\"title\": \"Cost-Efficiency\", \"impact\": \"This will maximize your ROI and make your marketing budget go further.\", \"description\": \"Our strategic and data-driven approach reduces wasteful spending, ensuring that your budget is utilized effectively.\"}, {\"title\": \"Advanced Performance Tracking\", \"impact\": \"This enables your e-commerce business to continuously improve its marketing efforts, leading to increased sales and profitability.\", \"description\": \"We offer real-time performance tracking and analytics, providing you with actionable insights to refine your marketing strategies.\"}]}',NULL,'{\"project\": {\"budget\": \"$1000.0\", \"timeline\": {\"phases\": [{\"phase\": \"Market Research\", \"duration\": \"1 month\", \"milestones\": [\"Identify target audience\", \"Analyze market trends\", \"Competitor analysis\"], \"deliverables\": [\"Market research report\", \"Target audience profile\", \"Competitor analysis report\"]}, {\"phase\": \"Strategy Development\", \"duration\": \"1 month\", \"milestones\": [\"Define marketing objectives\", \"Develop marketing strategies\", \"Create marketing budget\"], \"deliverables\": [\"Marketing plan\", \"Marketing budget\"]}, {\"phase\": \"Content Creation\", \"duration\": \"1 month\", \"milestones\": [\"Develop content calendar\", \"Create marketing materials\", \"Test marketing materials\"], \"deliverables\": [\"Content calendar\", \"Marketing materials\"]}, {\"phase\": \"Campaign Execution\", \"duration\": \"1 month\", \"milestones\": [\"Launch marketing campaign\", \"Monitor campaign performance\", \"Adjust campaign as necessary\"], \"deliverables\": [\"Launched campaign\", \"Campaign performance report\"]}, {\"phase\": \"Evaluation & Analysis\", \"duration\": \"1 month\", \"milestones\": [\"Collect campaign data\", \"Analyze campaign effectiveness\", \"Identify areas for improvement\"], \"deliverables\": [\"Campaign analysis report\", \"Improvement plan\"]}, {\"phase\": \"Revision & Optimization\", \"duration\": \"1 month\", \"milestones\": [\"Revise marketing strategies based on analysis\", \"Optimize future campaigns\", \"Finalize marketing report\"], \"deliverables\": [\"Revised marketing plan\", \"Optimized future campaign plans\", \"Final marketing report\"]}], \"total_duration\": \"6 months\"}}}',NULL,'sent','2025-11-15 16:32:29','2025-11-14 11:15:56','2025-11-17 04:31:42',1,'professional',NULL,NULL,NULL,'CALIM');
/*!40000 ALTER TABLE `project_proposals` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `proposal_share_links`
--

DROP TABLE IF EXISTS `proposal_share_links`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `proposal_share_links` (
  `share_id` int NOT NULL AUTO_INCREMENT,
  `proposal_id` int NOT NULL,
  `share_token` varchar(255) NOT NULL,
  `created_by` int NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `expires_at` timestamp NULL DEFAULT NULL,
  `view_count` int DEFAULT '0',
  `last_viewed_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`share_id`),
  UNIQUE KEY `share_token` (`share_token`),
  KEY `created_by` (`created_by`),
  KEY `idx_token` (`share_token`),
  KEY `idx_proposal` (`proposal_id`),
  CONSTRAINT `proposal_share_links_ibfk_1` FOREIGN KEY (`proposal_id`) REFERENCES `project_proposals` (`proposal_id`) ON DELETE CASCADE,
  CONSTRAINT `proposal_share_links_ibfk_2` FOREIGN KEY (`created_by`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `proposal_share_links`
--

LOCK TABLES `proposal_share_links` WRITE;
/*!40000 ALTER TABLE `proposal_share_links` DISABLE KEYS */;
INSERT INTO `proposal_share_links` VALUES (1,4,'EZi1GweTfHSQ2TvndmTANqGxytJsECwWlFfKMbmc4kk',1,'2025-11-13 08:22:01','2025-12-13 08:22:01',0,NULL),(2,4,'JmoFoIe4nljbcqacTaHZPUySP5CZOWyft6aXZGboopM',1,'2025-11-13 08:33:19','2025-12-13 08:33:19',0,NULL),(3,3,'jJ1KMcQGMDmvbTNYvq7uW5cijWZhZS1F2Qsv7oVsM1k',1,'2025-11-13 08:53:04','2025-12-13 08:53:04',0,NULL),(4,6,'bByAOh8BycRUxkkr-S-VRkU55UvnOAWeEv9WNQrT5ow',1,'2025-11-13 12:17:44','2025-12-13 12:17:44',0,NULL),(5,7,'vh2X9Z2JuPCQJ733NRA5I8eIjXXBkR_ri2mSd3zw9nQ',1,'2025-11-13 12:29:39','2025-12-13 12:29:39',0,NULL),(6,14,'KtUgIprVzkBQCEK0xgqQjoE-fOT-UGtWL8yQ6YJB6YM',1,'2025-11-14 11:39:15','2025-12-14 11:39:15',0,NULL),(7,14,'5zPEzXfBjhzTMfESihBy1UWZGS7riX1wWZMpaRGtI3w',1,'2025-11-14 12:05:52','2025-12-14 12:05:52',0,NULL),(8,14,'_5XXalcRL_7Nwloa8234m5qA_D1IPwoENGjGPu_mEpU',1,'2025-11-15 05:52:05','2025-12-15 05:52:05',0,NULL),(9,14,'_Np2-853zIuews7Agvh1naMSLWy-HVVIPSkRrRNjWos',1,'2025-11-15 16:32:16','2025-12-15 16:32:16',0,NULL),(10,14,'a84p2uQRkZXn2bjzDzH43jRx_BvtA6pEmdG_Gbe7Cio',1,'2025-11-17 04:31:51','2025-12-17 04:31:51',0,NULL);
/*!40000 ALTER TABLE `proposal_share_links` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `role_permissions`
--

DROP TABLE IF EXISTS `role_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `role_permissions` (
  `role_permission_id` int NOT NULL AUTO_INCREMENT,
  `role` enum('client','admin','employee') NOT NULL,
  `permission_id` int NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`role_permission_id`),
  UNIQUE KEY `unique_role_permission` (`role`,`permission_id`),
  KEY `permission_id` (`permission_id`),
  KEY `idx_role` (`role`),
  CONSTRAINT `role_permissions_ibfk_1` FOREIGN KEY (`permission_id`) REFERENCES `permissions` (`permission_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=101 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `role_permissions`
--

LOCK TABLES `role_permissions` WRITE;
/*!40000 ALTER TABLE `role_permissions` DISABLE KEYS */;
INSERT INTO `role_permissions` VALUES (1,'admin',7,'2025-11-16 00:34:37'),(2,'admin',8,'2025-11-16 00:34:37'),(3,'admin',9,'2025-11-16 00:34:37'),(4,'admin',41,'2025-11-16 00:34:37'),(5,'admin',42,'2025-11-16 00:34:37'),(6,'admin',43,'2025-11-16 00:34:37'),(7,'admin',44,'2025-11-16 00:34:37'),(8,'admin',45,'2025-11-16 00:34:37'),(9,'admin',46,'2025-11-16 00:34:37'),(10,'admin',10,'2025-11-16 00:34:37'),(11,'admin',11,'2025-11-16 00:34:37'),(12,'admin',12,'2025-11-16 00:34:37'),(13,'admin',13,'2025-11-16 00:34:37'),(14,'admin',24,'2025-11-16 00:34:37'),(15,'admin',25,'2025-11-16 00:34:37'),(16,'admin',26,'2025-11-16 00:34:37'),(17,'admin',27,'2025-11-16 00:34:37'),(18,'admin',28,'2025-11-16 00:34:37'),(19,'admin',29,'2025-11-16 00:34:37'),(20,'admin',30,'2025-11-16 00:34:37'),(21,'admin',31,'2025-11-16 00:34:37'),(22,'admin',47,'2025-11-16 00:34:37'),(23,'admin',48,'2025-11-16 00:34:37'),(24,'admin',39,'2025-11-16 00:34:37'),(25,'admin',40,'2025-11-16 00:34:37'),(26,'admin',49,'2025-11-16 00:34:37'),(27,'admin',50,'2025-11-16 00:34:37'),(28,'admin',20,'2025-11-16 00:34:37'),(29,'admin',21,'2025-11-16 00:34:37'),(30,'admin',22,'2025-11-16 00:34:37'),(31,'admin',23,'2025-11-16 00:34:37'),(32,'admin',36,'2025-11-16 00:34:37'),(33,'admin',37,'2025-11-16 00:34:37'),(34,'admin',38,'2025-11-16 00:34:37'),(35,'admin',32,'2025-11-16 00:34:37'),(36,'admin',33,'2025-11-16 00:34:37'),(37,'admin',34,'2025-11-16 00:34:37'),(38,'admin',35,'2025-11-16 00:34:37'),(39,'admin',14,'2025-11-16 00:34:37'),(40,'admin',15,'2025-11-16 00:34:37'),(41,'admin',16,'2025-11-16 00:34:37'),(42,'admin',17,'2025-11-16 00:34:37'),(43,'admin',18,'2025-11-16 00:34:37'),(44,'admin',19,'2025-11-16 00:34:37'),(45,'admin',1,'2025-11-16 00:34:37'),(46,'admin',2,'2025-11-16 00:34:37'),(47,'admin',3,'2025-11-16 00:34:37'),(48,'admin',4,'2025-11-16 00:34:37'),(49,'admin',5,'2025-11-16 00:34:37'),(50,'admin',6,'2025-11-16 00:34:37'),(64,'employee',42,'2025-11-16 00:34:37'),(65,'employee',43,'2025-11-16 00:34:37'),(66,'employee',41,'2025-11-16 00:34:37'),(67,'employee',45,'2025-11-16 00:34:37'),(68,'employee',25,'2025-11-16 00:34:37'),(69,'employee',26,'2025-11-16 00:34:37'),(70,'employee',27,'2025-11-16 00:34:37'),(71,'employee',24,'2025-11-16 00:34:37'),(72,'employee',12,'2025-11-16 00:34:37'),(73,'employee',11,'2025-11-16 00:34:37'),(74,'employee',29,'2025-11-16 00:34:37'),(75,'employee',30,'2025-11-16 00:34:37'),(76,'employee',31,'2025-11-16 00:34:37'),(77,'employee',28,'2025-11-16 00:34:37'),(78,'employee',40,'2025-11-16 00:34:37'),(79,'employee',39,'2025-11-16 00:34:37'),(80,'employee',21,'2025-11-16 00:34:37'),(81,'employee',22,'2025-11-16 00:34:37'),(82,'employee',20,'2025-11-16 00:34:37'),(83,'employee',38,'2025-11-16 00:34:37'),(84,'employee',37,'2025-11-16 00:34:37'),(85,'employee',36,'2025-11-16 00:34:37'),(86,'employee',33,'2025-11-16 00:34:37'),(87,'employee',35,'2025-11-16 00:34:37'),(88,'employee',34,'2025-11-16 00:34:37'),(89,'employee',32,'2025-11-16 00:34:37'),(90,'employee',17,'2025-11-16 00:34:37'),(91,'employee',15,'2025-11-16 00:34:37'),(95,'client',41,'2025-11-16 00:34:37'),(96,'client',45,'2025-11-16 00:34:37'),(97,'client',24,'2025-11-16 00:34:37'),(98,'client',28,'2025-11-16 00:34:37'),(99,'client',20,'2025-11-16 00:34:37'),(100,'client',32,'2025-11-16 00:34:37');
/*!40000 ALTER TABLE `role_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `segment_contacts`
--

DROP TABLE IF EXISTS `segment_contacts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `segment_contacts` (
  `contact_id` int NOT NULL AUTO_INCREMENT,
  `segment_id` int NOT NULL,
  `name` varchar(255) DEFAULT NULL,
  `email` varchar(255) DEFAULT NULL,
  `phone` varchar(50) DEFAULT NULL,
  `company` varchar(255) DEFAULT NULL,
  `additional_data` json DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`contact_id`),
  KEY `idx_segment_id` (`segment_id`),
  KEY `idx_email` (`email`),
  KEY `idx_phone` (`phone`),
  CONSTRAINT `segment_contacts_ibfk_1` FOREIGN KEY (`segment_id`) REFERENCES `audience_segments` (`segment_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `segment_contacts`
--

LOCK TABLES `segment_contacts` WRITE;
/*!40000 ALTER TABLE `segment_contacts` DISABLE KEYS */;
INSERT INTO `segment_contacts` VALUES (2,7,'Ilham Safeek','ilhamsafeek@yahoo.com','94777140803','','{}','2025-11-14 21:12:23'),(3,8,'Ilham Safeek','ilhamsafeek@yahoo.com','94777140803','','{}','2025-11-14 21:50:33');
/*!40000 ALTER TABLE `segment_contacts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `seo_analytics`
--

DROP TABLE IF EXISTS `seo_analytics`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `seo_analytics` (
  `seo_analytics_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `seo_project_id` int DEFAULT NULL,
  `metric_date` date NOT NULL,
  `metric_name` varchar(100) NOT NULL,
  `metric_value` decimal(12,2) DEFAULT NULL,
  `page_url` varchar(500) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`seo_analytics_id`),
  KEY `seo_project_id` (`seo_project_id`),
  KEY `idx_client_date` (`client_id`,`metric_date`),
  KEY `idx_metric_name` (`metric_name`),
  CONSTRAINT `seo_analytics_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `seo_analytics_ibfk_2` FOREIGN KEY (`seo_project_id`) REFERENCES `seo_projects` (`seo_project_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `seo_analytics`
--

LOCK TABLES `seo_analytics` WRITE;
/*!40000 ALTER TABLE `seo_analytics` DISABLE KEYS */;
/*!40000 ALTER TABLE `seo_analytics` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `seo_audits`
--

DROP TABLE IF EXISTS `seo_audits`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `seo_audits` (
  `audit_id` int NOT NULL AUTO_INCREMENT,
  `seo_project_id` int NOT NULL,
  `audit_date` date NOT NULL,
  `overall_score` decimal(5,2) DEFAULT NULL,
  `issues_found` json DEFAULT NULL,
  `recommendations` json DEFAULT NULL,
  `page_speed_score` decimal(5,2) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`audit_id`),
  KEY `seo_project_id` (`seo_project_id`),
  CONSTRAINT `seo_audits_ibfk_1` FOREIGN KEY (`seo_project_id`) REFERENCES `seo_projects` (`seo_project_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `seo_audits`
--

LOCK TABLES `seo_audits` WRITE;
/*!40000 ALTER TABLE `seo_audits` DISABLE KEYS */;
INSERT INTO `seo_audits` VALUES (1,1,'2025-11-15',75.00,'[{\"severity\": \"critical\", \"description\": \"Missing XML sitemap\"}, {\"severity\": \"warning\", \"description\": \"Missing alt tags on some images\"}, {\"severity\": \"info\", \"description\": \"Page load time is slightly above average\"}]','[\"Create an XML sitemap to help search engines better crawl your site\", \"Add alt tags to all images to improve accessibility and SEO\", \"Optimize your site\'s load time to improve user experience\"]',0.00,'2025-11-15 11:33:34'),(2,1,'2025-11-15',75.00,'[{\"severity\": \"critical\", \"description\": \"The website is not HTTPS secure\"}, {\"severity\": \"warning\", \"description\": \"Some images are missing alt tags\"}, {\"severity\": \"info\", \"description\": \"The website does not have an XML sitemap\"}]','[\"Switch to HTTPS to improve security\", \"Add alt tags to all images for improved accessibility\", \"Create an XML sitemap to help search engines crawl your site more effectively\"]',0.00,'2025-11-15 15:10:07'),(3,1,'2025-11-15',75.00,'[{\"severity\": \"critical\", \"description\": \"HTTPS not implemented\"}, {\"severity\": \"warning\", \"description\": \"Images missing alt tags\"}, {\"severity\": \"info\", \"description\": \"Page load time is above average\"}]','[\"Implement HTTPS for secure connections\", \"Add alt tags to all images for accessibility\", \"Optimize images and scripts to reduce page load time\"]',0.00,'2025-11-15 16:39:25'),(4,1,'2025-11-17',75.00,'[{\"severity\": \"critical\", \"description\": \"Website is not fully optimized for mobile view\"}, {\"severity\": \"warning\", \"description\": \"Missing alt tags on several images\"}, {\"severity\": \"info\", \"description\": \"Some internal links are broken\"}]','[\"Optimize website for mobile view\", \"Add alt tags to all images\", \"Fix all broken internal links\"]',0.00,'2025-11-17 04:47:57');
/*!40000 ALTER TABLE `seo_audits` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `seo_metrics`
--

DROP TABLE IF EXISTS `seo_metrics`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `seo_metrics` (
  `seo_metric_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `metric_date` date NOT NULL,
  `domain_authority` int DEFAULT '0',
  `page_authority` int DEFAULT '0',
  `spam_score` int DEFAULT '0',
  `backlinks_count` int DEFAULT '0',
  `referring_domains` int DEFAULT '0',
  `organic_keywords` int DEFAULT '0',
  `organic_traffic` int DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`seo_metric_id`),
  UNIQUE KEY `unique_client_date` (`client_id`,`metric_date`),
  KEY `idx_client_date` (`client_id`,`metric_date`),
  CONSTRAINT `seo_metrics_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `seo_metrics`
--

LOCK TABLES `seo_metrics` WRITE;
/*!40000 ALTER TABLE `seo_metrics` DISABLE KEYS */;
/*!40000 ALTER TABLE `seo_metrics` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `seo_projects`
--

DROP TABLE IF EXISTS `seo_projects`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `seo_projects` (
  `seo_project_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `website_url` varchar(500) NOT NULL,
  `target_keywords` json DEFAULT NULL,
  `current_domain_authority` decimal(5,2) DEFAULT NULL,
  `status` enum('active','paused') DEFAULT 'active',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`seo_project_id`),
  KEY `idx_client_id` (`client_id`),
  CONSTRAINT `seo_projects_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `seo_projects`
--

LOCK TABLES `seo_projects` WRITE;
/*!40000 ALTER TABLE `seo_projects` DISABLE KEYS */;
INSERT INTO `seo_projects` VALUES (1,1,'https://hashnate.com/','[\"ERP\"]',NULL,'active','2025-11-15 11:26:25');
/*!40000 ALTER TABLE `seo_projects` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `social_media_analytics`
--

DROP TABLE IF EXISTS `social_media_analytics`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `social_media_analytics` (
  `analytics_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `platform` varchar(50) NOT NULL,
  `metric_date` date NOT NULL,
  `followers_count` int DEFAULT '0',
  `impressions` int DEFAULT '0',
  `reach` int DEFAULT '0',
  `engagement_count` int DEFAULT '0',
  `trending_topics` json DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`analytics_id`),
  UNIQUE KEY `unique_client_platform_date` (`client_id`,`platform`,`metric_date`),
  CONSTRAINT `social_media_analytics_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `social_media_analytics`
--

LOCK TABLES `social_media_analytics` WRITE;
/*!40000 ALTER TABLE `social_media_analytics` DISABLE KEYS */;
/*!40000 ALTER TABLE `social_media_analytics` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `social_media_posts`
--

DROP TABLE IF EXISTS `social_media_posts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `social_media_posts` (
  `post_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `content_id` int DEFAULT NULL,
  `created_by` int NOT NULL,
  `platform` varchar(50) NOT NULL,
  `caption` text,
  `media_urls` json DEFAULT NULL,
  `hashtags` json DEFAULT NULL,
  `scheduled_at` timestamp NULL DEFAULT NULL,
  `published_at` timestamp NULL DEFAULT NULL,
  `status` enum('draft','scheduled','published') DEFAULT 'draft',
  `external_post_id` varchar(255) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`post_id`),
  KEY `content_id` (`content_id`),
  KEY `created_by` (`created_by`),
  KEY `idx_client_platform` (`client_id`,`platform`),
  KEY `idx_scheduled_at` (`scheduled_at`),
  CONSTRAINT `social_media_posts_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `social_media_posts_ibfk_2` FOREIGN KEY (`content_id`) REFERENCES `content_library` (`content_id`),
  CONSTRAINT `social_media_posts_ibfk_3` FOREIGN KEY (`created_by`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `social_media_posts`
--

LOCK TABLES `social_media_posts` WRITE;
/*!40000 ALTER TABLE `social_media_posts` DISABLE KEYS */;
INSERT INTO `social_media_posts` VALUES (1,17,NULL,1,'instagram','testing','[]','[]','2025-11-19 07:30:00',NULL,'scheduled',NULL,'2025-11-15 10:34:36');
/*!40000 ALTER TABLE `social_media_posts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `system_settings`
--

DROP TABLE IF EXISTS `system_settings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `system_settings` (
  `setting_id` int NOT NULL AUTO_INCREMENT,
  `setting_key` varchar(100) NOT NULL,
  `setting_value` text,
  `setting_category` enum('api','general','email','notification') DEFAULT 'general',
  `is_encrypted` tinyint(1) DEFAULT '0',
  `updated_by` int DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`setting_id`),
  UNIQUE KEY `setting_key` (`setting_key`),
  KEY `updated_by` (`updated_by`),
  KEY `idx_category` (`setting_category`),
  KEY `idx_key` (`setting_key`),
  CONSTRAINT `system_settings_ibfk_1` FOREIGN KEY (`updated_by`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `system_settings`
--

LOCK TABLES `system_settings` WRITE;
/*!40000 ALTER TABLE `system_settings` DISABLE KEYS */;
INSERT INTO `system_settings` VALUES (1,'openai_api_key',NULL,'api',1,NULL,'2025-11-16 18:15:44'),(2,'meta_app_id',NULL,'api',0,NULL,'2025-11-16 18:15:44'),(3,'meta_app_secret',NULL,'api',1,NULL,'2025-11-16 18:15:44'),(4,'meta_access_token',NULL,'api',1,NULL,'2025-11-16 18:15:44'),(5,'google_client_id',NULL,'api',0,NULL,'2025-11-16 18:15:44'),(6,'google_client_secret',NULL,'api',1,NULL,'2025-11-16 18:15:44'),(7,'google_ads_developer_token',NULL,'api',1,NULL,'2025-11-16 18:15:44'),(8,'mailchimp_api_key',NULL,'api',1,NULL,'2025-11-16 18:15:44'),(9,'whatsapp_business_api_key',NULL,'api',1,NULL,'2025-11-16 18:15:44'),(10,'whatsapp_phone_number_id',NULL,'api',0,NULL,'2025-11-16 18:15:44'),(11,'synthesia_api_key',NULL,'api',1,NULL,'2025-11-16 18:15:44'),(12,'canva_api_key',NULL,'api',1,NULL,'2025-11-16 18:15:44'),(13,'dalle_api_key',NULL,'api',1,NULL,'2025-11-16 18:15:44'),(14,'linkedin_client_id',NULL,'api',0,NULL,'2025-11-16 18:15:44'),(15,'linkedin_client_secret',NULL,'api',1,NULL,'2025-11-16 18:15:44'),(16,'moz_access_id',NULL,'api',0,NULL,'2025-11-16 18:15:44'),(17,'moz_secret_key',NULL,'api',1,NULL,'2025-11-16 18:15:44'),(18,'google_analytics_property_id',NULL,'api',0,NULL,'2025-11-16 18:15:44'),(19,'company_name',NULL,'general',0,NULL,'2025-11-16 18:15:44'),(20,'company_logo_url',NULL,'general',0,NULL,'2025-11-16 18:15:44'),(21,'smtp_host',NULL,'email',0,NULL,'2025-11-16 18:15:44'),(22,'smtp_port',NULL,'email',0,NULL,'2025-11-16 18:15:44'),(23,'smtp_username',NULL,'email',0,NULL,'2025-11-16 18:15:44'),(24,'smtp_password',NULL,'email',1,NULL,'2025-11-16 18:15:44');
/*!40000 ALTER TABLE `system_settings` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tasks`
--

DROP TABLE IF EXISTS `tasks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tasks` (
  `task_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `assigned_to` int DEFAULT NULL,
  `assigned_by` int NOT NULL,
  `task_title` varchar(255) NOT NULL,
  `task_description` text,
  `priority` enum('low','medium','high','urgent') DEFAULT 'medium',
  `status` enum('pending','in_progress','completed') DEFAULT 'pending',
  `due_date` date DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`task_id`),
  KEY `client_id` (`client_id`),
  KEY `assigned_by` (`assigned_by`),
  KEY `idx_assigned_to` (`assigned_to`),
  KEY `idx_status` (`status`),
  CONSTRAINT `tasks_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `tasks_ibfk_2` FOREIGN KEY (`assigned_to`) REFERENCES `users` (`user_id`),
  CONSTRAINT `tasks_ibfk_3` FOREIGN KEY (`assigned_by`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tasks`
--

LOCK TABLES `tasks` WRITE;
/*!40000 ALTER TABLE `tasks` DISABLE KEYS */;
INSERT INTO `tasks` VALUES (1,17,3,1,'efref','weft','high','pending','2025-11-16','2025-11-16 14:58:48','2025-11-17 04:54:29');
/*!40000 ALTER TABLE `tasks` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `top_pages`
--

DROP TABLE IF EXISTS `top_pages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `top_pages` (
  `page_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `page_url` text NOT NULL,
  `page_title` varchar(500) DEFAULT NULL,
  `metric_date` date NOT NULL,
  `pageviews` int DEFAULT '0',
  `unique_pageviews` int DEFAULT '0',
  `avg_time_on_page` int DEFAULT '0',
  `bounce_rate` decimal(5,2) DEFAULT '0.00',
  `page_authority` int DEFAULT '0',
  `external_links` int DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`page_id`),
  KEY `idx_client_date` (`client_id`,`metric_date`),
  KEY `idx_pageviews` (`pageviews` DESC),
  CONSTRAINT `top_pages_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `top_pages`
--

LOCK TABLES `top_pages` WRITE;
/*!40000 ALTER TABLE `top_pages` DISABLE KEYS */;
/*!40000 ALTER TABLE `top_pages` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `trending_topics`
--

DROP TABLE IF EXISTS `trending_topics`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `trending_topics` (
  `trend_id` int NOT NULL AUTO_INCREMENT,
  `platform` varchar(50) NOT NULL,
  `topic` varchar(255) NOT NULL,
  `category` varchar(100) DEFAULT NULL,
  `volume` int DEFAULT NULL,
  `detected_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`trend_id`),
  KEY `idx_platform` (`platform`),
  KEY `idx_detected_at` (`detected_at`)
) ENGINE=InnoDB AUTO_INCREMENT=46 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `trending_topics`
--

LOCK TABLES `trending_topics` WRITE;
/*!40000 ALTER TABLE `trending_topics` DISABLE KEYS */;
INSERT INTO `trending_topics` VALUES (1,'instagram','marketing','Hashtag',50000000,'2025-11-15 10:18:50'),(2,'instagram','socialmedia','Hashtag',30000000,'2025-11-15 10:18:50'),(3,'instagram','digitalmarketing','Hashtag',25000000,'2025-11-15 10:18:50'),(4,'instagram','contentcreator','Hashtag',20000000,'2025-11-15 10:18:50'),(5,'instagram','entrepreneur','Hashtag',18000000,'2025-11-15 10:18:50'),(6,'facebook','Metaverse Expansion','Technology',230000,'2025-11-15 10:18:57'),(7,'facebook','Thanksgiving Recipes 2025','Food & Drink',120000,'2025-11-15 10:18:57'),(8,'facebook','Climate Change Summit Outcomes','Environment',150000,'2025-11-15 10:18:57'),(9,'facebook','Black Friday Deals 2025','Shopping',200000,'2025-11-15 10:18:57'),(10,'facebook','COVID-19 Pandemic Fifth Year','Health & Wellness',180000,'2025-11-15 10:18:57'),(11,'linkedin','AI Content Creation','Technology',125000,'2025-11-15 10:19:01'),(12,'linkedin','Holiday Marketing 2025','Marketing',98000,'2025-11-15 10:19:01'),(13,'linkedin','Sustainable Business Practices','Business',150000,'2025-11-15 10:19:01'),(14,'linkedin','Remote Work Culture','Human Resources',135000,'2025-11-15 10:19:01'),(15,'linkedin','Metaverse in Business','Innovation',120000,'2025-11-15 10:19:01'),(16,'twitter','#ClimateChangeConference2025','Environment',165000,'2025-11-15 10:19:06'),(17,'twitter','Metaverse Expansion','Technology',142000,'2025-11-15 10:19:06'),(18,'twitter','#ThanksgivingRecipes2025','Food & Drink',110000,'2025-11-15 10:19:06'),(19,'twitter','Black Friday Deals 2025','Shopping',200000,'2025-11-15 10:19:06'),(20,'twitter','#Movember2025','Health',135000,'2025-11-15 10:19:06'),(21,'pinterest','DIY Thanksgiving Decor','Home Decor',150000,'2025-11-15 10:26:12'),(22,'pinterest','Winter Fashion Trends 2025','Fashion',200000,'2025-11-15 10:26:12'),(23,'pinterest','Vegan Holiday Recipes','Food & Drink',120000,'2025-11-15 10:26:12'),(24,'pinterest','Sustainable Gift Wrapping','Sustainability',90000,'2025-11-15 10:26:12'),(25,'pinterest','Black Friday Shopping Tips','Shopping',130000,'2025-11-15 10:26:12'),(26,'instagram','marketing','Hashtag',50000000,'2025-11-16 13:43:41'),(27,'instagram','socialmedia','Hashtag',30000000,'2025-11-16 13:43:41'),(28,'instagram','digitalmarketing','Hashtag',25000000,'2025-11-16 13:43:41'),(29,'instagram','contentcreator','Hashtag',20000000,'2025-11-16 13:43:41'),(30,'instagram','entrepreneur','Hashtag',18000000,'2025-11-16 13:43:41'),(31,'facebook','#MetaverseExplorations','Technology',210000,'2025-11-16 13:43:49'),(32,'facebook','ThanksgivingRecipes2025','Food & Drink',150000,'2025-11-16 13:43:49'),(33,'facebook','BlackFridayDeals2025','Shopping',190000,'2025-11-16 13:43:49'),(34,'facebook','ClimateChangeConference','Environment',135000,'2025-11-16 13:43:49'),(35,'facebook','Election2026Prep','Politics',120000,'2025-11-16 13:43:49'),(36,'linkedin','Green Business Practices','Sustainability',150000,'2025-11-16 13:43:56'),(37,'linkedin','The Future of Remote Work','Workplace Culture',135000,'2025-11-16 13:43:56'),(38,'linkedin','Crypto in Business Transactions','Finance',120000,'2025-11-16 13:43:56'),(39,'linkedin','Diversity in Tech 2025','Diversity & Inclusion',110000,'2025-11-16 13:43:56'),(40,'linkedin','AI in Healthcare','Healthcare',105000,'2025-11-16 13:43:56'),(41,'twitter','#Thanksgiving2025','Holiday',210000,'2025-11-16 13:44:01'),(42,'twitter','Metaverse Real Estate','Technology',180000,'2025-11-16 13:44:01'),(43,'twitter','Climate Change Conference 2025 Highlights','Environment',160000,'2025-11-16 13:44:01'),(44,'twitter','AI in Healthcare 2025','Healthcare',140000,'2025-11-16 13:44:01'),(45,'twitter','#BlackFridayDeals2025','Shopping',220000,'2025-11-16 13:44:01');
/*!40000 ALTER TABLE `trending_topics` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `triggered_flows`
--

DROP TABLE IF EXISTS `triggered_flows`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `triggered_flows` (
  `flow_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `created_by` int NOT NULL,
  `flow_name` varchar(255) NOT NULL,
  `trigger_type` varchar(100) NOT NULL,
  `trigger_conditions` json DEFAULT NULL,
  `flow_actions` json DEFAULT NULL,
  `channel` varchar(50) NOT NULL,
  `is_active` tinyint(1) DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`flow_id`),
  KEY `created_by` (`created_by`),
  KEY `idx_client_id` (`client_id`),
  CONSTRAINT `triggered_flows_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `triggered_flows_ibfk_2` FOREIGN KEY (`created_by`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `triggered_flows`
--

LOCK TABLES `triggered_flows` WRITE;
/*!40000 ALTER TABLE `triggered_flows` DISABLE KEYS */;
/*!40000 ALTER TABLE `triggered_flows` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_activity_log`
--

DROP TABLE IF EXISTS `user_activity_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_activity_log` (
  `activity_id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `activity_type` varchar(100) NOT NULL,
  `module` varchar(50) DEFAULT NULL,
  `description` text,
  `ip_address` varchar(45) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`activity_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_activity_type` (`activity_type`),
  KEY `idx_created_at` (`created_at`),
  CONSTRAINT `user_activity_log_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_activity_log`
--

LOCK TABLES `user_activity_log` WRITE;
/*!40000 ALTER TABLE `user_activity_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `user_activity_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_permissions`
--

DROP TABLE IF EXISTS `user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_permissions` (
  `user_permission_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `permission_id` int NOT NULL,
  `granted` tinyint(1) DEFAULT '1',
  `granted_by` int DEFAULT NULL,
  `granted_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `expires_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`user_permission_id`),
  UNIQUE KEY `unique_user_permission` (`user_id`,`permission_id`),
  KEY `permission_id` (`permission_id`),
  KEY `granted_by` (`granted_by`),
  KEY `idx_user_id` (`user_id`),
  CONSTRAINT `user_permissions_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `user_permissions_ibfk_2` FOREIGN KEY (`permission_id`) REFERENCES `permissions` (`permission_id`) ON DELETE CASCADE,
  CONSTRAINT `user_permissions_ibfk_3` FOREIGN KEY (`granted_by`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_permissions`
--

LOCK TABLES `user_permissions` WRITE;
/*!40000 ALTER TABLE `user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `user_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_sessions`
--

DROP TABLE IF EXISTS `user_sessions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_sessions` (
  `session_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `token` varchar(500) NOT NULL,
  `ip_address` varchar(45) DEFAULT NULL,
  `expires_at` timestamp NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`session_id`),
  KEY `user_id` (`user_id`),
  KEY `idx_token` (`token`(255)),
  CONSTRAINT `user_sessions_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_sessions`
--

LOCK TABLES `user_sessions` WRITE;
/*!40000 ALTER TABLE `user_sessions` DISABLE KEYS */;
INSERT INTO `user_sessions` VALUES (1,3,'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlbXBsb3llZUBwYW52ZWxpcS5jb20iLCJ1c2VyX2lkIjozLCJyb2xlIjoiZW1wbG95ZWUiLCJleHAiOjE3NjMwOTYwMzJ9.UNTb2U5NnICt50W-SPTefEjhCsoLOenbfuAMCghr8Bw','127.0.0.1','2025-11-13 23:23:53','2025-11-13 04:53:52'),(2,3,'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlbXBsb3llZUBwYW52ZWxpcS5jb20iLCJ1c2VyX2lkIjozLCJyb2xlIjoiZW1wbG95ZWUiLCJleHAiOjE3NjMwOTYxMzh9.f--AePq_WafNilXroIc6A7ZlGtvDP5NFej1-dUxaVVg','127.0.0.1','2025-11-13 23:25:38','2025-11-13 04:55:38'),(3,3,'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlbXBsb3llZUBwYW52ZWxpcS5jb20iLCJ1c2VyX2lkIjozLCJyb2xlIjoiZW1wbG95ZWUiLCJleHAiOjE3NjMwOTYxNTV9.YJAlXs-eN4KrdzDbQanpix-oZWEp1BEkQFRCkgh3AsM','127.0.0.1','2025-11-13 23:25:55','2025-11-13 04:55:55'),(4,3,'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlbXBsb3llZUBwYW52ZWxpcS5jb20iLCJ1c2VyX2lkIjozLCJyb2xlIjoiZW1wbG95ZWUiLCJleHAiOjE3NjMwOTYyNTN9.0np6r-afNQdPuYqupMsTigmurxtaEh9gyFuiuzbCnh0','127.0.0.1','2025-11-13 23:27:34','2025-11-13 04:57:33'),(5,3,'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlbXBsb3llZUBwYW52ZWxpcS5jb20iLCJ1c2VyX2lkIjozLCJyb2xlIjoiZW1wbG95ZWUiLCJleHAiOjE3NjMwOTYzMzV9.XSa4BJjeJgdCr4IQujwn3GYWu3qHjO243S9vM9WiNMQ','127.0.0.1','2025-11-13 23:28:55','2025-11-13 04:58:55'),(6,3,'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlbXBsb3llZUBwYW52ZWxpcS5jb20iLCJ1c2VyX2lkIjozLCJyb2xlIjoiZW1wbG95ZWUiLCJleHAiOjE3NjMwOTY0MTd9.nf3oYXeNLzPm8PzVXm67kqyROU9aD5KFfGPQc312iBQ','127.0.0.1','2025-11-13 23:30:18','2025-11-13 05:00:17'),(7,3,'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlbXBsb3llZUBwYW52ZWxpcS5jb20iLCJ1c2VyX2lkIjozLCJyb2xlIjoiZW1wbG95ZWUiLCJleHAiOjE3NjMwOTY1OTB9.AS6rVmxxqre7yxKHwEQnNnr4aFaifQGAzzLFOtCowZo','127.0.0.1','2025-11-13 23:33:10','2025-11-13 05:03:10'),(8,3,'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlbXBsb3llZUBwYW52ZWxpcS5jb20iLCJ1c2VyX2lkIjozLCJyb2xlIjoiZW1wbG95ZWUiLCJleHAiOjE3NjMwOTY2ODN9.QlbEVXYavuLgbwopW4Q0ovGBFuPYbXo1YCEXynVY5gQ','127.0.0.1','2025-11-13 23:34:44','2025-11-13 05:04:43'),(9,3,'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlbXBsb3llZUBwYW52ZWxpcS5jb20iLCJ1c2VyX2lkIjozLCJyb2xlIjoiZW1wbG95ZWUiLCJleHAiOjE3NjMwOTY3OTN9.QshtAolA4jZ0z6wGXkZQSedbPB--5fcL8eEaY0v3xGc','127.0.0.1','2025-11-13 23:36:34','2025-11-13 05:06:33'),(10,3,'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlbXBsb3llZUBwYW52ZWxpcS5jb20iLCJ1c2VyX2lkIjozLCJyb2xlIjoiZW1wbG95ZWUiLCJleHAiOjE3NjMwOTY4MTN9.dd9fgRp6VUy03PsxM67C-ztafWpKVrxdunPV1A4sLIg','127.0.0.1','2025-11-13 23:36:53','2025-11-13 05:06:53');
/*!40000 ALTER TABLE `user_sessions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `user_id` int NOT NULL AUTO_INCREMENT,
  `email` varchar(255) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `full_name` varchar(255) NOT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `role` enum('client','admin','employee') NOT NULL,
  `status` enum('pending','active','suspended','inactive') DEFAULT 'pending',
  `profile_image` varchar(500) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_login` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `email` (`email`),
  KEY `idx_email` (`email`),
  KEY `idx_role` (`role`),
  KEY `idx_status` (`status`)
) ENGINE=InnoDB AUTO_INCREMENT=24 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'admin@panveliq.com','$2b$12$zGAKg4Y72wfR.9FMR7R26eCXWvNyag2gkQRw8cKCut9UanZOKyIr6','Admin User',NULL,'admin','active',NULL,'2025-11-12 19:35:13','2025-11-17 08:57:06','2025-11-17 08:57:06'),(2,'ilham@gmail.com','$2b$12$VIiIX0lu.VgD8JRSl54lMu0seBFAXK/NJwoMl/pnKFCCGl0prpyye','Ilham Safeek','0777140803','client','active',NULL,'2025-11-12 19:38:55','2025-11-17 08:56:41','2025-11-17 08:56:41'),(3,'employee@panveliq.com','$2b$12$zGAKg4Y72wfR.9FMR7R26eCXWvNyag2gkQRw8cKCut9UanZOKyIr6','Mohamed Faris',NULL,'employee','active',NULL,'2025-11-12 20:39:10','2025-11-17 09:00:14','2025-11-17 09:00:14'),(4,'linson.doe@example.com','','Linson Dominic',NULL,'client','pending',NULL,'2025-11-13 06:42:47','2025-11-13 06:42:47',NULL),(5,'keethan@gmail.com','','Keethan',NULL,'client','active',NULL,'2025-11-13 07:02:52','2025-11-13 08:36:33',NULL),(6,'sakeena@gmail.com','','Sakeena',NULL,'client','pending',NULL,'2025-11-13 07:09:22','2025-11-13 07:09:22',NULL),(7,'ilham@hashnate.com','','Ilham',NULL,'client','pending',NULL,'2025-11-13 07:32:41','2025-11-13 07:32:41',NULL),(8,'tester@gmail.com','','Tester',NULL,'client','pending',NULL,'2025-11-13 08:43:50','2025-11-13 08:43:50',NULL),(9,'faris@hashnate.com','','Faris',NULL,'client','pending',NULL,'2025-11-13 08:57:05','2025-11-13 08:57:05',NULL),(10,'sameeha@gmail.com','','sameeha',NULL,'client','pending',NULL,'2025-11-13 12:03:18','2025-11-13 12:03:18',NULL),(11,'aathifa@gmail.com','','Aathifa',NULL,'client','pending',NULL,'2025-11-13 12:36:51','2025-11-13 12:36:51',NULL),(12,'lafir@gmail.com','','Lafir',NULL,'client','pending',NULL,'2025-11-14 05:56:10','2025-11-14 05:56:10',NULL),(13,'aakifa@hashnate.com','','Aakifa Niyas',NULL,'client','pending',NULL,'2025-11-14 06:25:39','2025-11-14 06:25:39',NULL),(14,'abu@gmail.com','','Abu Nasar',NULL,'client','pending',NULL,'2025-11-14 11:15:56','2025-11-14 11:15:56',NULL),(15,'ilhamsafeek@yahoo.com','$2b$12$BOU2/5isXHrHls77EU7IjuGp77Rk2p9bLh1kfmo7Jo0BCa3Rqy9g2','Ilham S','0777140803','client','pending',NULL,'2025-11-14 12:59:08','2025-11-14 12:59:08',NULL),(16,'ilhamsa@gmail.com','$2b$12$frD0XtWMz9qYArtz7XtXpOBZ1QPU6Bq3MQq2Kl5EPhiLa7JNkeR/.','Ilham Sa','0777140803','client','pending',NULL,'2025-11-14 13:10:46','2025-11-14 13:10:46',NULL),(17,'umar@gmail.com','$2b$12$doVSYRal4Qr3omViPo7Gxe9b9BRGUdeSZ3Y78WAf/SDDv6/TKAZvi','Umar Rajeeh','0775899077','client','active',NULL,'2025-11-14 13:43:04','2025-11-17 08:34:32','2025-11-17 08:34:32'),(18,'saud@gmail.com','$2b$12$Gbl.pdCn4iVvL27NlihhFuWngMmked4VITo5C1NSE2EevFgACgViq','M Saud','07771243546','client','pending',NULL,'2025-11-17 04:32:46','2025-11-17 04:32:46',NULL),(19,'tester1@gmail.com','$2b$12$5.XXHhNKRIZ2f12mSrbLOOulsureLE2T.r5654KJYkccgOpwX5Bw.','Tester Me','0777130803','client','pending',NULL,'2025-11-17 05:23:00','2025-11-17 06:43:04','2025-11-17 05:23:42'),(20,'ilhamsafeek@gmail.com','$2b$12$WFT1Gk48H/VbpTU1h.58x.jZX5ty/tQK.tYIWo8Tg1A5cBR7n4/y6','ilham safe','0777140803','client','pending',NULL,'2025-11-17 06:36:56','2025-11-17 06:36:56',NULL),(21,'aakifaniyas@gmail.com','$2b$12$/xcvZ5IH5Gllbq6B1l1RZuBdQqDo8N5Bw./g6T3uS6VfLwW5NSzJ6','Aakifa Niyas','0777590840','client','pending',NULL,'2025-11-17 08:25:17','2025-11-17 08:25:17',NULL),(22,'ishan@gmail.com','$2b$12$EgeQEh1X7hUZsQ8gIBSugOY6EHA8LleqdiBsyZigTbWaVSiOZZkxO','Ishan Shanaf','07773498573','client','active',NULL,'2025-11-17 08:28:00','2025-11-17 08:28:01','2025-11-17 08:28:01'),(23,'user@gmail.com','$2b$12$SKTtsLllmvSQJhBBCTTcQe3x8tuCWFwGdKQSRaFc7NCieKtPDm3uO','Testing User','07753538563','client','active',NULL,'2025-11-17 12:11:16','2025-11-17 12:11:16','2025-11-17 12:11:16');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `website_traffic`
--

DROP TABLE IF EXISTS `website_traffic`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `website_traffic` (
  `traffic_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `metric_date` date NOT NULL,
  `sessions` int DEFAULT '0',
  `users` int DEFAULT '0',
  `new_users` int DEFAULT '0',
  `pageviews` int DEFAULT '0',
  `bounce_rate` decimal(5,2) DEFAULT '0.00',
  `avg_session_duration` int DEFAULT '0',
  `organic_sessions` int DEFAULT '0',
  `paid_sessions` int DEFAULT '0',
  `social_sessions` int DEFAULT '0',
  `direct_sessions` int DEFAULT '0',
  `referral_sessions` int DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`traffic_id`),
  UNIQUE KEY `unique_client_date` (`client_id`,`metric_date`),
  KEY `idx_client_date` (`client_id`,`metric_date`),
  CONSTRAINT `website_traffic_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `website_traffic`
--

LOCK TABLES `website_traffic` WRITE;
/*!40000 ALTER TABLE `website_traffic` DISABLE KEYS */;
/*!40000 ALTER TABLE `website_traffic` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `whatsapp_campaigns`
--

DROP TABLE IF EXISTS `whatsapp_campaigns`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `whatsapp_campaigns` (
  `campaign_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `created_by` int NOT NULL,
  `campaign_name` varchar(255) NOT NULL,
  `template_name` varchar(255) DEFAULT NULL,
  `message_content` text,
  `schedule_type` enum('immediate','scheduled') DEFAULT 'scheduled',
  `scheduled_at` timestamp NULL DEFAULT NULL,
  `status` enum('draft','scheduled','sent','failed') DEFAULT 'draft',
  `total_recipients` int DEFAULT '0',
  `delivered_count` int DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`campaign_id`),
  KEY `created_by` (`created_by`),
  KEY `idx_client_id` (`client_id`),
  CONSTRAINT `whatsapp_campaigns_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `whatsapp_campaigns_ibfk_2` FOREIGN KEY (`created_by`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `whatsapp_campaigns`
--

LOCK TABLES `whatsapp_campaigns` WRITE;
/*!40000 ALTER TABLE `whatsapp_campaigns` DISABLE KEYS */;
INSERT INTO `whatsapp_campaigns` VALUES (1,17,1,'yttt','','Hi \n\nFrom Panvel','immediate',NULL,'sent',1,0,'2025-11-14 17:52:58'),(2,17,1,'yttt','','Hi \n\nFrom Panvel','immediate',NULL,'sent',1,0,'2025-11-14 17:54:19'),(3,17,1,'afqdfedw','','afweafweaf','immediate',NULL,'sent',1,0,'2025-11-14 18:03:46'),(4,17,1,'afqdfedw','','afweafweaf','immediate',NULL,'draft',1,0,'2025-11-14 18:08:56'),(5,17,1,'sfdfe','','Hi,\n\nthis is from Panvel','immediate',NULL,'draft',1,0,'2025-11-14 18:09:38'),(6,17,1,'sfdfe','','Hi,\n\nthis is from Panvel','immediate',NULL,'draft',1,0,'2025-11-14 18:11:54'),(7,17,1,'Test','','Tsting from Panvel','immediate',NULL,'draft',1,0,'2025-11-14 18:12:24'),(8,17,1,'Test','','Tsting from Panvel','immediate',NULL,'draft',1,0,'2025-11-14 18:13:36'),(9,17,1,'Test','','Tsting from Panvel','immediate',NULL,'draft',1,0,'2025-11-14 18:13:45'),(10,17,1,'Hi Test','','Hi \n\nthis is From Panvel','immediate',NULL,'sent',1,0,'2025-11-14 18:15:00'),(11,17,1,'Ho','','From Panvel ','immediate',NULL,'draft',1,0,'2025-11-14 18:20:37'),(12,17,1,'Ho','','From Panvel ','immediate',NULL,'sent',1,0,'2025-11-14 18:21:12');
/*!40000 ALTER TABLE `whatsapp_campaigns` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-11-18 11:29:57
