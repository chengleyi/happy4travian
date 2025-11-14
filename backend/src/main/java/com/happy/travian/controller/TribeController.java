package com.happy.travian.controller;

import com.happy.travian.domain.Tribe;
import com.happy.travian.dto.CreateTribeRequest;
import com.happy.travian.repository.TribeRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/v1/tribes")
public class TribeController {
  private final TribeRepository repo;
  public TribeController(TribeRepository repo) { this.repo = repo; }

  @GetMapping
  public List<Tribe> list() { return repo.findAll(); }

  @PostMapping
  public ResponseEntity<Tribe> create(@RequestBody CreateTribeRequest req) {
    if (req.getCode() == null || req.getCode().isEmpty()) return ResponseEntity.badRequest().build();
    if (req.getName() == null || req.getName().isEmpty()) return ResponseEntity.badRequest().build();
    var t = new Tribe();
    t.setCode(req.getCode());
    t.setName(req.getName());
    return ResponseEntity.ok(repo.save(t));
  }
}