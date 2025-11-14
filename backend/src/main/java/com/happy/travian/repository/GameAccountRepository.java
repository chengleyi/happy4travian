package com.happy.travian.repository;

import com.happy.travian.domain.GameAccount;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface GameAccountRepository extends JpaRepository<GameAccount, Long> {
  List<GameAccount> findByUserId(Long userId);
  List<GameAccount> findByServerId(Long serverId);
}