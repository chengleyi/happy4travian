package com.happy.travian.repository;

import com.happy.travian.domain.User;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;

public interface UserRepository extends JpaRepository<User, Long> {
  Optional<User> findByWechatOpenid(String wechatOpenid);
}