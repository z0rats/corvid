import React from "react";
import Card from '@mui/material/Card';
import Grow from '@mui/material/Grow';
import Skeleton from '@mui/material/Skeleton';
import Stack from '@mui/material/Stack';
export default function NewsfeedSkeleton({ pageSize }) {
  return (
    <>
      {[...Array(pageSize)].map((e, i) => (
        <span key={i}>
          <Grow in={true} key={`grow-loading-${i}`}>
            <Card
              sx={{
                mb: 2,
                p: 2,
                borderRadius: 1,
                boxShadow: 0,
              }}
              key={`card-loading-${i}`}
            >
              <Stack spacing={1}>
                <Stack direction="row" spacing={1}>
                  <Skeleton
                    variant="circular"
                    animation="wave"
                    width={50}
                    height={50}
                  />
                  <Stack spacing={0} width={"30%"}>
                    <Skeleton
                      variant="text"
                      animation="wave"
                      width={"60%"}
                      sx={{ fontSize: "1rem" }}
                    />
                    <Skeleton
                      variant="text"
                      animation="wave"
                      width={"100%"}
                      sx={{ fontSize: "1rem" }}
                    />
                  </Stack>
                </Stack>
                <Skeleton
                  variant="text"
                  animation="wave"
                  width={"60%"}
                  sx={{ fontSize: "3rem" }}
                />
                <Skeleton
                  variant="rounded"
                  animation="wave"
                  width={"100%"}
                  height={120}
                />
              </Stack>
            </Card>
          </Grow>
        </span>
      ))}
    </>
  );
}
