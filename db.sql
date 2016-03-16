-- phpMyAdmin SQL Dump
-- version 4.4.10
-- http://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: Nov 13, 2015 at 03:39 PM
-- Server version: 5.5.42
-- PHP Version: 5.6.10

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";

--
-- Database: `service_layer`
--

-- --------------------------------------------------------

--
-- Table structure for table `node`
--

CREATE TABLE IF NOT EXISTS `node` (
  `id` varchar(64) NOT NULL,
  `name` varchar(64) NOT NULL,
  `domain_id` varchar(64) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `session`
--

CREATE TABLE IF NOT EXISTS `session` (
  `id` varchar(64) NOT NULL,
  `user_id` varchar(64) DEFAULT NULL,
  `service_graph_id` varchar(64) NOT NULL,
  `service_graph_name` varchar(64) NOT NULL,
  `ingress_node` varchar(64) DEFAULT NULL,
  `egress_node` varchar(64) DEFAULT NULL,
  `status` varchar(64) NOT NULL,
  `started_at` datetime DEFAULT NULL,
  `last_update` datetime DEFAULT NULL,
  `error` datetime DEFAULT NULL,
  `ended` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `user`
--

CREATE TABLE IF NOT EXISTS `user` (
  `id` varchar(64) CHARACTER SET utf8 NOT NULL,
  `name` varchar(64) CHARACTER SET utf8 NOT NULL,
  `password` varchar(64) CHARACTER SET utf8 NOT NULL,
  `tenant_id` varchar(64) CHARACTER SET utf8 NOT NULL,
  `mail` varchar(64) CHARACTER SET utf8 DEFAULT NULL,
  `service_graph` text NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `tenant`
--

CREATE TABLE IF NOT EXISTS `tenant` (
  `id` varchar(64) CHARACTER SET utf8 NOT NULL,
  `name` varchar(64) CHARACTER SET utf8 NOT NULL,
  `description` varchar(128) CHARACTER SET utf8 NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `vnf_image`
--

CREATE TABLE IF NOT EXISTS `vnf_image` (
  `id` varchar(255) NOT NULL,
  `internal_id` varchar(255) NOT NULL,
  `template` text NOT NULL,
  `configuration_model` text,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `user_device`
--

CREATE TABLE IF NOT EXISTS `user_device` (
  `session_id` varchar(64) NOT NULL,
  `mac_address` varchar(64) NOT NULL,
  PRIMARY KEY (`session_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


--
-- Dumping data for table `node`
--

REPLACE INTO `user` (`id`, `name`, `password`, `tenant_id`) VALUES
('0', 'user1', 'password1', 'public');

--
-- Dumping data for table `user`
--

REPLACE INTO `node` (`id`, `name`, `domain_id`) VALUES
('0', 'node0', '130.192.225.105'),
('1', 'node1', '130.192.225.193'),
('2', 'node2', '10.0.0.3'),
('3', 'node3', '10.0.0.4'),
('4', 'node4', '10.0.0.5');

--
-- Dumping data for table `tenant`
--

REPLACE INTO `tenant` (`id`, `name`, `description`) VALUES
('public', 'public', 'public tenant');


