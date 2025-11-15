package com.happy.travian.controller;

import com.happy.travian.domain.TroopCount;
import com.happy.travian.dto.UploadTroopsRequest;
import com.happy.travian.repository.TroopCountRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.*;

@RestController
@RequestMapping("/api/v1/troops")
public class TroopController {
  private final TroopCountRepository countRepo;
  public TroopController(TroopCountRepository countRepo) { this.countRepo = countRepo; }

  @PostMapping("/upload")
  public ResponseEntity<String> upload(@RequestBody UploadTroopsRequest req) {
    if (req.getVillageId() == null || req.getCounts() == null) return ResponseEntity.badRequest().build();
    for (var e : req.getCounts().entrySet()) {
      var tc = new TroopCount();
      tc.setVillageId(req.getVillageId());
      tc.setTroopTypeId(e.getKey());
      tc.setCount(e.getValue());
      countRepo.save(tc);
    }
    return ResponseEntity.ok("ok");
  }

  @GetMapping("/aggregate")
  public ResponseEntity<Map<Integer, Long>> aggregate(@RequestParam Long villageId) {
    try {
      var list = countRepo.findByVillageId(villageId);
      var map = new HashMap<Integer, Long>();
      for (var tc : list) {
        map.put(tc.getTroopTypeId(), tc.getCount());
      }
      return ResponseEntity.ok(map);
    } catch (Exception e) {
      return ResponseEntity.ok(new HashMap<>());
    }
  }
}