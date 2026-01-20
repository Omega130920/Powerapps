-- MySQL dump 10.13  Distrib 8.0.43, for Win64 (x86_64)
--
-- Host: localhost    Database: pssubf_db
-- ------------------------------------------------------
-- Server version	8.0.43

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add log entry',1,'add_logentry'),(2,'Can change log entry',1,'change_logentry'),(3,'Can delete log entry',1,'delete_logentry'),(4,'Can view log entry',1,'view_logentry'),(5,'Can add permission',2,'add_permission'),(6,'Can change permission',2,'change_permission'),(7,'Can delete permission',2,'delete_permission'),(8,'Can view permission',2,'view_permission'),(9,'Can add group',3,'add_group'),(10,'Can change group',3,'change_group'),(11,'Can delete group',3,'delete_group'),(12,'Can view group',3,'view_group'),(13,'Can add user',4,'add_user'),(14,'Can change user',4,'change_user'),(15,'Can delete user',4,'delete_user'),(16,'Can view user',4,'view_user'),(17,'Can add content type',5,'add_contenttype'),(18,'Can change content type',5,'change_contenttype'),(19,'Can delete content type',5,'delete_contenttype'),(20,'Can view content type',5,'view_contenttype'),(21,'Can add session',6,'add_session'),(22,'Can change session',6,'change_session'),(23,'Can delete session',6,'delete_session'),(24,'Can view session',6,'view_session');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user`
--

DROP TABLE IF EXISTS `auth_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user`
--

LOCK TABLES `auth_user` WRITE;
/*!40000 ALTER TABLE `auth_user` DISABLE KEYS */;
INSERT INTO `auth_user` VALUES (1,'pbkdf2_sha256$1000000$5TT8Ai0Ecn0NnvZ9aks6JG$80TqknYKS17rpOmhKKKl2u2Ga9haAbGN+/Dbyw4lcLQ=','2026-01-15 09:23:50.021569',1,'omega','','','',1,1,'2026-01-06 10:01:53.589111');
/*!40000 ALTER TABLE `auth_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_groups`
--

DROP TABLE IF EXISTS `auth_user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_groups` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`,`group_id`),
  KEY `auth_user_groups_group_id_97559544_fk_auth_group_id` (`group_id`),
  CONSTRAINT `auth_user_groups_group_id_97559544_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `auth_user_groups_user_id_6a12ed8b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_groups`
--

LOCK TABLES `auth_user_groups` WRITE;
/*!40000 ALTER TABLE `auth_user_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_user_permissions`
--

DROP TABLE IF EXISTS `auth_user_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_user_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  KEY `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_user_permissions`
--

LOCK TABLES `auth_user_user_permissions` WRITE;
/*!40000 ALTER TABLE `auth_user_user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (1,'admin','logentry'),(3,'auth','group'),(2,'auth','permission'),(4,'auth','user'),(5,'contenttypes','contenttype'),(6,'sessions','session');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_migrations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'contenttypes','0001_initial','2026-01-06 09:54:27.039538'),(2,'auth','0001_initial','2026-01-06 09:54:28.159045'),(3,'admin','0001_initial','2026-01-06 09:54:28.516534'),(4,'admin','0002_logentry_remove_auto_add','2026-01-06 09:54:28.526272'),(5,'admin','0003_logentry_add_action_flag_choices','2026-01-06 09:54:28.536739'),(6,'contenttypes','0002_remove_content_type_name','2026-01-06 09:54:28.746733'),(7,'auth','0002_alter_permission_name_max_length','2026-01-06 09:54:28.856835'),(8,'auth','0003_alter_user_email_max_length','2026-01-06 09:54:28.906424'),(9,'auth','0004_alter_user_username_opts','2026-01-06 09:54:28.916837'),(10,'auth','0005_alter_user_last_login_null','2026-01-06 09:54:29.051990'),(11,'auth','0006_require_contenttypes_0002','2026-01-06 09:54:29.056051'),(12,'auth','0007_alter_validators_add_error_messages','2026-01-06 09:54:29.066238'),(13,'auth','0008_alter_user_username_max_length','2026-01-06 09:54:29.196179'),(14,'auth','0009_alter_user_last_name_max_length','2026-01-06 09:54:29.324064'),(15,'auth','0010_alter_group_name_max_length','2026-01-06 09:54:29.366117'),(16,'auth','0011_update_proxy_permissions','2026-01-06 09:54:29.377597'),(17,'auth','0012_alter_user_first_name_max_length','2026-01-06 09:54:29.520743'),(18,'sessions','0001_initial','2026-01-06 09:54:29.592396');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
INSERT INTO `django_session` VALUES ('grd55doliaf4il9qeq2z33n972c2a8oj','.eJxVjL0OwiAYAN-F2ZBCS6GO7n2G5vtDqgaS0k7GdzckHXS9u9xbLXDsaTmqbMvK6qqMuvwyBHpKboIfkO9FU8n7tqJuiT5t1XNhed3O9m-QoKa2RW9sJ2PgYCF6kR6t5YHDxNF3gMYYD2idEwIjOFrnScJAGCfA3pP6fAHwwjiz:1vd45u:2Rq6b4ihSXZQ1-wOM-XDMzlmjDIhdUL0-qSusf1cyJ8','2026-01-20 10:15:18.155196'),('v99o904lq68yb6qg6uxmjym06dvgoa7m','.eJxVjL0OwiAYAN-F2ZBCS6GO7n2G5vtDqgaS0k7GdzckHXS9u9xbLXDsaTmqbMvK6qqMuvwyBHpKboIfkO9FU8n7tqJuiT5t1XNhed3O9m-QoKa2RW9sJ2PgYCF6kR6t5YHDxNF3gMYYD2idEwIjOFrnScJAGCfA3pP6fAHwwjiz:1vgJa2:rJMDjNcmCMcgcWL_k4P8xdd7FsCBXC2qCDliWwTTdbI','2026-01-29 09:23:50.024422');
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pssubf_actions`
--

DROP TABLE IF EXISTS `pssubf_actions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pssubf_actions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `task_email_id` varchar(255) NOT NULL,
  `action_type` varchar(100) NOT NULL,
  `action_user` varchar(100) NOT NULL,
  `note_content` text,
  `action_timestamp` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pssubf_actions`
--

LOCK TABLES `pssubf_actions` WRITE;
/*!40000 ALTER TABLE `pssubf_actions` DISABLE KEYS */;
INSERT INTO `pssubf_actions` VALUES (1,'AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAYsUfNAAA=','Recycle','omega','PSSUBF Task Recycled by omega','2026-01-06 11:23:59'),(2,'AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAYsUfMAAA=','Delegation','omega','PSSUBF Task Delegated by omega','2026-01-06 11:27:03'),(3,'AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAYsUfLAAA=','Delegation','omega','PSSUBF Task Delegated by omega','2026-01-06 12:40:08'),(4,'AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAYsUfLAAA=','EMAIL_REPLY','omega','Sent reply to luano@futurasa.co.za with 0 files.',NULL),(5,'AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAYsUfNAAA=','Delegation','omega','PSSUBF Task Delegated by omega','2026-01-06 13:05:34');
/*!40000 ALTER TABLE `pssubf_actions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pssubf_delegate`
--

DROP TABLE IF EXISTS `pssubf_delegate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pssubf_delegate` (
  `email_id` varchar(255) NOT NULL,
  `assigned_agent` varchar(150) DEFAULT NULL,
  `member_group_code` varchar(100) DEFAULT NULL,
  `email_category` varchar(100) DEFAULT NULL,
  `subject` varchar(255) DEFAULT NULL,
  `sender` varchar(255) DEFAULT NULL,
  `status` varchar(50) DEFAULT 'Assigned',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`email_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pssubf_delegate`
--

LOCK TABLES `pssubf_delegate` WRITE;
/*!40000 ALTER TABLE `pssubf_delegate` DISABLE KEYS */;
INSERT INTO `pssubf_delegate` VALUES ('AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAYsUfLAAA=','omega','','Query','Re: test 11','testuser@futurasa.co.za','Delegated','2026-01-06 12:40:08'),('AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAYsUfMAAA=','omega','',NULL,NULL,NULL,'Delegated','2026-01-06 11:27:03'),('AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAYsUfNAAA=','','','Query','TEST ATT','luano@futurasa.co.za','Delegated','2026-01-06 13:05:34');
/*!40000 ALTER TABLE `pssubf_delegate` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pssubf_inbox`
--

DROP TABLE IF EXISTS `pssubf_inbox`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pssubf_inbox` (
  `email_id` varchar(255) NOT NULL,
  `subject` varchar(255) NOT NULL,
  `sender` varchar(255) NOT NULL,
  `received_timestamp` datetime NOT NULL,
  `snippet` text,
  `status` varchar(50) DEFAULT 'Pending',
  PRIMARY KEY (`email_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pssubf_inbox`
--

LOCK TABLES `pssubf_inbox` WRITE;
/*!40000 ALTER TABLE `pssubf_inbox` DISABLE KEYS */;
INSERT INTO `pssubf_inbox` VALUES ('AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAMKkyaAAA=','Query: Levy ','testuser@futurasa.co.za','2025-12-17 08:50:32','hello','Pending'),('AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAMKkybAAA=','Query: Levy ','testuser@futurasa.co.za','2025-12-17 08:52:20','hello','Pending'),('AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAMKkycAAA=','[MIP: 22117] Levy Query','testuser@futurasa.co.za','2025-12-17 08:52:31','                                    <p>Dear Sir/Madam,</p>\r\n                                    <p>Regarding Levy Number 22117 (ZMRHAL INVESTMENTS (PTY) LTD),</p>\r\n                                    <p><br></p>\r\n                                    <p>K','Pending'),('AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAMKkydAAA=','RE: [MIP: 1510022] New Direct Communication...','testuser@futurasa.co.za','2025-12-17 13:15:33','Testing 101','Pending'),('AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAMKkyVAAA=','Query: Levy 22117','testuser@futurasa.co.za','2025-12-17 08:36:24','dfgh','Pending'),('AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAMKkyWAAA=','Query: Levy 22117','testuser@futurasa.co.za','2025-12-17 08:37:07','dfgh','Pending'),('AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAMKkyXAAA=','Query: Levy 22117','testuser@futurasa.co.za','2025-12-17 08:38:32','dfgh','Pending'),('AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAMKkyYAAA=','Query: Levy 22117','testuser@futurasa.co.za','2025-12-17 08:39:53','dfgh','Pending'),('AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAMKkyZAAA=','Query: Levy ','testuser@futurasa.co.za','2025-12-17 08:48:27','hello','Pending'),('AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAANp2uAAAA=','[MIP: FAR0396] New Communication','testuser@futurasa.co.za','2025-12-19 12:20:41','Dear Sir/Madam,\r\n\r\nRegarding Member Group Code FAR0396,\r\n\r\n\r\nKind regards,\r\n\r\nomega','Pending'),('AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAANp2uBAAA=','[MIP: FAR0396] New Communication','testuser@futurasa.co.za','2025-12-19 12:20:57','Dear Sir/Madam,\r\n\r\nRegarding Member Group Code FAR0396,\r\n\r\n\r\nKind regards,\r\n\r\nomega','Pending'),('AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAQfgU_AAA=','TSRF_recon_app','luano@futurasa.co.za','2025-12-24 06:03:19','Good Morning\r\n\r\nThis is a test email for TSRF_recon_app\r\n\r\nKind regards\r\n\r\nLuano van Eck\r\nDebt Collection Team Leader\r\n\r\nemail: luano@futurasa.co.za\r\n\r\nDisclaimer: Futura SA Administrators (Pty) Ltd is an authorized Financial Services Provider licensed by','Pending'),('AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAQfgU-AAA=','Unity_internal','luano@futurasa.co.za','2025-12-24 06:03:50','Good Morning\r\n\r\nThis is a test email for Unity_internal\r\n\r\nKind regards\r\n\r\nLuano van Eck\r\nDebt Collection Team Leader\r\n\r\nemail: luano@futurasa.co.za\r\n\r\nDisclaimer: Futura SA Administrators (Pty) Ltd is an authorized Financial Services Provider licensed by','Pending'),('AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAQfgU6AAA=','RE: RE: [MIP: 1510022] New Direct Communication...','testuser@futurasa.co.za','2025-12-23 09:44:33','Hello how are you','Pending'),('AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAQfgU7AAA=','RE: RE: [MIP: 1510022] New Direct Communication...','testuser@futurasa.co.za','2025-12-23 09:45:08','Good day','Pending'),('AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAQfgU8AAA=','ACVV','luano@futurasa.co.za','2025-12-24 06:01:32','Good Morning\r\n\r\nThis is a test email for ACVV\r\n\r\nKind regards\r\n\r\nLuano van Eck\r\nDebt Collection Team Leader\r\n\r\nemail: luano@futurasa.co.za\r\n\r\nDisclaimer: Futura SA Administrators (Pty) Ltd is an authorized Financial Services Provider licensed by the Finan','Pending'),('AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAQfgU9AAA=','CRM_unity','luano@futurasa.co.za','2025-12-24 06:02:30','Good Morning\r\n\r\nThis is a test email for CRM_unity\r\n\r\nKind regards\r\n\r\nLuano van Eck\r\nDebt Collection Team Leader\r\n\r\nemail: luano@futurasa.co.za\r\n\r\nDisclaimer: Futura SA Administrators (Pty) Ltd is an authorized Financial Services Provider licensed by the ','Pending'),('AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAYsUfLAAA=','Re: test 11','testuser@futurasa.co.za','2026-01-04 19:34:19','vdgfhdfgbjkbn','Delegated'),('AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAYsUfMAAA=','Attachment Test','luano@futurasa.co.za','2026-01-04 21:10:56','Attachment test\r\n\r\n\r\nLuano van Eck\r\nDebt Collection Team Leader\r\n\r\nemail: luano@futurasa.co.za\r\n\r\nDisclaimer: Futura SA Administrators (Pty) Ltd is an authorized Financial Services Provider licensed by the Financial Sector Conduct Authority in terms of th','Delegated'),('AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAYsUfNAAA=','TEST ATT','luano@futurasa.co.za','2026-01-05 06:38:46','TEST ATT\r\n\r\nLuano van Eck\r\nDebt Collection Team Leader\r\n\r\nemail: luano@futurasa.co.za\r\n\r\nDisclaimer: Futura SA Administrators (Pty) Ltd is an authorized Financial Services Provider licensed by the Financial Sector Conduct Authority in terms of the FAIS ','Delegated');
/*!40000 ALTER TABLE `pssubf_inbox` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pssubf_outlook_token`
--

DROP TABLE IF EXISTS `pssubf_outlook_token`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pssubf_outlook_token` (
  `id` int NOT NULL AUTO_INCREMENT,
  `service_account` varchar(100) NOT NULL,
  `access_token` text NOT NULL,
  `expires_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `service_account` (`service_account`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pssubf_outlook_token`
--

LOCK TABLES `pssubf_outlook_token` WRITE;
/*!40000 ALTER TABLE `pssubf_outlook_token` DISABLE KEYS */;
INSERT INTO `pssubf_outlook_token` VALUES (1,'testuser@futurasa.co.za','eyJ0eXAiOiJKV1QiLCJub25jZSI6ImR5M0E3RGxfNUhVS3ZrQUR5cUl2c3duTC03bVRNMFd2RzdGUm5sU1pldGsiLCJhbGciOiJSUzI1NiIsIng1dCI6IlBjWDk4R1g0MjBUMVg2c0JEa3poUW1xZ3dNVSIsImtpZCI6IlBjWDk4R1g0MjBUMVg2c0JEa3poUW1xZ3dNVSJ9.eyJhdWQiOiJodHRwczovL2dyYXBoLm1pY3Jvc29mdC5jb20iLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC83YmNmYzA4MC1lMWYxLTRmOTktYjRlZC1lMWE5NmVkYTg5Y2UvIiwiaWF0IjoxNzY4NDY4MzQ3LCJuYmYiOjE3Njg0NjgzNDcsImV4cCI6MTc2ODQ3MjI0NywiYWlvIjoiazJaZ1lIaWo2NWtYc1c3R0tSZmR2WldWRTNzWEF3QT0iLCJhcHBfZGlzcGxheW5hbWUiOiJGdXR1cmEtQXBwIiwiYXBwaWQiOiI5ZjgyZTU3ZC00NWE0LTRiNjYtYWIyOS04YTliMzgxYTA4MmEiLCJhcHBpZGFjciI6IjEiLCJpZHAiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC83YmNmYzA4MC1lMWYxLTRmOTktYjRlZC1lMWE5NmVkYTg5Y2UvIiwiaWR0eXAiOiJhcHAiLCJvaWQiOiI0MTc2NDgyNy0yZGJlLTRiMTYtYWJhNi0xZDIwMDYxYjU5MWYiLCJyaCI6IjEuQVNBQWdNRFBlX0hobVUtMDdlR3BidHFKemdNQUFBQUFBQUFBd0FBQUFBQUFBQUE5QVFBZ0FBLiIsInJvbGVzIjpbIk1haWwuUmVhZCIsIk1haWwuU2VuZCJdLCJzdWIiOiI0MTc2NDgyNy0yZGJlLTRiMTYtYWJhNi0xZDIwMDYxYjU5MWYiLCJ0ZW5hbnRfcmVnaW9uX3Njb3BlIjoiQUYiLCJ0aWQiOiI3YmNmYzA4MC1lMWYxLTRmOTktYjRlZC1lMWE5NmVkYTg5Y2UiLCJ1dGkiOiJ0WHZ2Q0N5aWxVV25TZURJWGZnRkFBIiwidmVyIjoiMS4wIiwid2lkcyI6WyIwOTk3YTFkMC0wZDFkLTRhY2ItYjQwOC1kNWNhNzMxMjFlOTAiXSwieG1zX2FjZCI6MTc2NDE2MDkyNiwieG1zX2FjdF9mY3QiOiI5IDMiLCJ4bXNfZnRkIjoiOGpRNkdwRDYybW1sVHVGUGhWZ0JyZG5sMExLWFVpcjRyYnVYclNndWs3d0JjM2RsWkdWdVl5MWtjMjF6IiwieG1zX2lkcmVsIjoiNyAyMiIsInhtc19yZCI6IjAuNDJMbFlCSmlWQkFTNFdBWEV2aFM4X2Ria2R4T3g1bF9jajdPVU42bUJ4VGxGQko0MjVBY0Z0TFQ3RDVkZ2VGMVdWbXRMMUNVUTBpQW1RRUNEa0JwQUEiLCJ4bXNfc3ViX2ZjdCI6IjMgOSIsInhtc190Y2R0IjoxNDk5NzEyNDIwLCJ4bXNfdG50X2ZjdCI6IjMgNCJ9.Y-FFrDktSeAibUMNUzavPH1hRtC55uPp8h60T6yFyuI7iASeEDSpv_xJ2FCzSGO07bgb_n599nyXNa75eY3pMqeexdueFH9midWbMOOJyCGsI6aoz0tV9CcyS1NgpPHXGbERKzAwHy79pJ31eW2ikcJ3PoppXSdBfp7Cto2O_8GjGPuovqxaR7QgrzSHx8opNCiivHFDDwVLgLSPi1NnVDjIY7tsIpRiXOzg8YCi_Qv5uX1pZAbqCOd8R6QIiIO30dGV4HBD1RP1EUGrfDHF1rH0D7UWj8BlIwA0SnFeH_NXQRnrQKVhCGRCB5_QC7yVnYkRfbJxWPDmFWhdffnuoA','2026-01-15 10:17:26');
/*!40000 ALTER TABLE `pssubf_outlook_token` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-01-20 15:18:29
