package com.happy.travian.controller;

import com.happy.travian.domain.GameAccount;
import com.happy.travian.dto.CreateGameAccountRequest;
import com.happy.travian.repository.GameAccountRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/v1/accounts")
public class GameAccountController {
  private final GameAccountRepository repo;
  public GameAccountController(GameAccountRepository repo) { this.repo = repo; }

  @GetMapping
  public List<GameAccount> list(@RequestParam(required = false) Long userId,
                                @RequestParam(required = false) Long serverId) {
    if (userId != null) return repo.findByUserId(userId);
    if (serverId != null) return repo.findByServerId(serverId);
    return repo.findAll();
  }

  @PostMapping
  public ResponseEntity<GameAccount> create(@RequestBody CreateGameAccountRequest req) {
    if (req.getUserId() == null || req.getServerId() == null || req.getTribeId() == null || req.getInGameName() == null) return ResponseEntity.badRequest().build();
    var a = new GameAccount();
    a.setUserId(req.getUserId());
    a.setServerId(req.getServerId());
    a.setTribeId(req.getTribeId());
    a.setInGameName(req.getInGameName());
    return ResponseEntity.ok(repo.save(a));
  }
}