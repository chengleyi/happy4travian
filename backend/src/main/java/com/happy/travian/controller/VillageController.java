package com.happy.travian.controller;

import com.happy.travian.domain.Village;
import com.happy.travian.dto.CreateVillageRequest;
import com.happy.travian.repository.VillageRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/v1/villages")
public class VillageController {
  private final VillageRepository repo;
  public VillageController(VillageRepository repo) { this.repo = repo; }

  @GetMapping
  public List<Village> list(@RequestParam(required = false) Long serverId,
                            @RequestParam(required = false) Long gameAccountId) {
    if (serverId != null) return repo.findByServerId(serverId);
    if (gameAccountId != null) return repo.findByGameAccountId(gameAccountId);
    return repo.findAll();
  }

  @PostMapping
  public ResponseEntity<Village> create(@RequestBody CreateVillageRequest req) {
    if (req.getServerId() == null || req.getGameAccountId() == null || req.getName() == null || req.getX() == null || req.getY() == null) return ResponseEntity.badRequest().build();
    var v = new Village();
    v.setServerId(req.getServerId());
    v.setGameAccountId(req.getGameAccountId());
    v.setName(req.getName());
    v.setX(req.getX());
    v.setY(req.getY());
    return ResponseEntity.ok(repo.save(v));
  }
}