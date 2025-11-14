package com.happy.travian.controller;

import jakarta.annotation.Resource;
import javax.sql.DataSource;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1")
public class DbController {
  @Resource
  private DataSource dataSource;

  @GetMapping("/db/ping")
  public ResponseEntity<String> ping() {
    try (var conn = dataSource.getConnection()) {
      var meta = conn.getMetaData();
      var product = meta.getDatabaseProductName();
      return ResponseEntity.ok(product);
    } catch (Exception e) {
      return ResponseEntity.status(500).body("error");
    }
  }
}