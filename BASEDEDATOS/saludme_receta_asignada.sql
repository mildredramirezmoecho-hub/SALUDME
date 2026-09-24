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
-- Table structure for table `receta_asignada`
--

DROP TABLE IF EXISTS `receta_asignada`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `receta_asignada` (
  `id_asignar_r` int NOT NULL AUTO_INCREMENT,
  `id_recetas` int DEFAULT NULL,
  `id_Pacientes` int NOT NULL,
  `id_profesional` int NOT NULL,
  `fecha_asignacion` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_asignar_r`),
  KEY `id_recetas` (`id_recetas`),
  KEY `id_Pacientes` (`id_Pacientes`),
  KEY `id_profesional` (`id_profesional`),
  CONSTRAINT `receta_asignada_ibfk_1` FOREIGN KEY (`id_recetas`) REFERENCES `recetas` (`id_recetas`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `receta_asignada_ibfk_2` FOREIGN KEY (`id_Pacientes`) REFERENCES `pacientes` (`id_Pacientes`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `receta_asignada_ibfk_3` FOREIGN KEY (`id_profesional`) REFERENCES `profesional` (`id_profesional`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `receta_asignada`
--

LOCK TABLES `receta_asignada` WRITE;
/*!40000 ALTER TABLE `receta_asignada` DISABLE KEYS */;
INSERT INTO `receta_asignada` VALUES (1,3,1,1,'2025-07-07 00:00:00'),(2,3,1,1,'2025-07-07 00:00:00'),(12,6,1,1,'2025-07-16 00:00:00');
/*!40000 ALTER TABLE `receta_asignada` ENABLE KEYS */;
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
