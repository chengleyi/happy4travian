package com.happy.travian.controller;

import com.happy.travian.repository.ServerRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/db")
public class DbController {
  private final ServerRepository serverRepository;
  public DbController(ServerRepository serverRepository) { this.serverRepository = serverRepository; }

  @GetMapping("/ping")
  public ResponseEntity<String> ping() {
    try {
      serverRepository.count();
      return ResponseEntity.ok("ok");
    } catch (Exception e) {
      return ResponseEntity.status(500).body("error");
    }
  }
}