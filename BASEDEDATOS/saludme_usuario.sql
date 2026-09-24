-- MySQL dump 10.13  Distrib 8.0.42, for Win64 (x86_64)
--
-- Host: localhost    Database: saludme
-- ------------------------------------------------------
-- Server version	8.0.42

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `usuario`
--

DROP TABLE IF EXISTS `usuario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuario` (
  `id_usuario` int NOT NULL AUTO_INCREMENT,
  `email` varchar(100) NOT NULL,
  `contraseña_hash` varchar(200) NOT NULL,
  `rol` varchar(50) NOT NULL,
  `telefono` varchar(15) DEFAULT NULL,
  `id_empresa` int DEFAULT NULL,
  PRIMARY KEY (`id_usuario`),
  UNIQUE KEY `email` (`email`),
  KEY `id_empresa` (`id_empresa`),
  CONSTRAINT `usuario_ibfk_1` FOREIGN KEY (`id_empresa`) REFERENCES `empresa` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=60 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuario`
--

LOCK TABLES `usuario` WRITE;
/*!40000 ALTER TABLE `usuario` DISABLE KEYS */;
INSERT INTO `usuario` VALUES (4,'ana.martinez@saludme.com','scrypt:32768:8:1$hpvasBrVGEF6RO2I$de28db3f67e14bcdf78ed620e45d0678c0b37c6f88b4d1526d5e9104b782a8234b184314bc4ac28b6950a09cbc83ff63600baed12876bba0cc4dc099cecf9e82','Profesional','0941946351',1),(5,'pablo.torres@saludme.com','scrypt:32768:8:1$oJRd1uDnDsIiTa1k$49be0b55042aa535f730130dca427a66d9453d313bfd814fdd4ce3d74bbbf5f95d0c178e0d0b4af81a4e344632275a92b4c5c2c3e9e3c4850745b9bbf8443b7f','Profesional','0965214568',1),(6,'carolina.lopez@saludme.com','scrypt:32768:8:1$33DPqJsunZ3X8iSX$ffd9366f2a86c59c3b965b577b1490249a3905cbced6c969f346e6c9b61225c5ba8cd6f790568d234850cd4495e6b33964754ee83a0f73d7c1236174a31e38c8','Profesional','0975368425',1),(7,'millyae99@gmail.com','scrypt:32768:8:1$NosTmOrECgxITMR5$8dd90402d474c9a13db493380f15f9031f91881eac7f830589c904a00f29bd7992e73c09f5abb2bf80b0a5d7685d9705bc080aa0aa912eadfc3762fbc1589214','Paciente',NULL,NULL),(8,'personal@saludme.com','scrypt:32768:8:1$XLZKRpiN3FHFTGQL$7ab78aede5e401e52524d353a80ce6cd193607770cf6bfbeae6ef762ea503ff405db76f222aca5f634405f1f1a98a2dbac96926ef150ce9359d73592286654d2','Personal','096698214',1),(58,'demi.silva.sr2020@gmail.com','scrypt:32768:8:1$wQF8028jdMGs34kJ$d8108241053956d4dc51306712a2603d4c8c71877dab7063ae2060cb7c4e2095fb678ec2a8f00d3393a82a31a3cbf9497f6a111f8b456f250b03f8d2bf44381e','Profesional','0993375043',NULL),(59,'yoMIL@gmail.com','scrypt:32768:8:1$BQwRHeV2lxLdaybE$04d91c16d7ddd6d2c7ee7255633cb662e874c91034b19c3c3174669c267c090b6ec7f8527e8a16ad584f5af43440ae8ebc71f6565fd67b06fec477f0c367f63a','Paciente','0941943755',NULL);
/*!40000 ALTER TABLE `usuario` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-01-09 23:24:01
