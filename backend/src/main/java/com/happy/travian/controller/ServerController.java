package com.happy.travian.controller;

import com.happy.travian.domain.Server;
import com.happy.travian.dto.CreateServerRequest;
import com.happy.travian.repository.ServerRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.*;
import java.time.LocalDate;
import java.util.List;

@RestController
@RequestMapping("/api/v1/servers")
public class ServerController {
  private final ServerRepository repo;
  public ServerController(ServerRepository repo) { this.repo = repo; }

  @GetMapping
  public List<Server> list() { return repo.findAll(); }

  @PostMapping
  public ResponseEntity<Server> create(@RequestBody CreateServerRequest req) {
    if (req.getCode() == null || req.getCode().isEmpty()) return ResponseEntity.badRequest().build();
    var s = new Server();
    s.setCode(req.getCode());
    s.setRegion(req.getRegion());
    s.setSpeed(req.getSpeed());
    if (req.getStartDate() != null && !req.getStartDate().isEmpty()) s.setStartDate(LocalDate.parse(req.getStartDate()));
    s.setStatus("active");
    return ResponseEntity.ok(repo.save(s));
  }

  @PostMapping(path = "/form", consumes = MediaType.APPLICATION_FORM_URLENCODED_VALUE)
  public ResponseEntity<Server> createForm(@ModelAttribute CreateServerRequest req) {
    if (req.getCode() == null || req.getCode().isEmpty()) return ResponseEntity.badRequest().build();
    var s = new Server();
    s.setCode(req.getCode());
    s.setRegion(req.getRegion());
    s.setSpeed(req.getSpeed());
    if (req.getStartDate() != null && !req.getStartDate().isEmpty()) s.setStartDate(LocalDate.parse(req.getStartDate()));
    s.setStatus("active");
    return ResponseEntity.ok(repo.save(s));
  }
}